import asyncio
import json
import multiprocessing
import os
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote as url_quote
from uuid import uuid4
from typing import Dict, List, Optional, Set

import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AnyHttpUrl

from backend.db import (
    create_scrape_job,
    insert_scrape_result,
    update_scrape_job_status,
    fetch_raw_materials,
    fetch_formulas,
    fetch_scrape_results,
    fetch_stats,
    create_raw_material,
    create_formula,
    create_formula_ingredient,
    fetch_formula_with_ingredients,
    fetch_all_inci_names,
    fetch_all_scrape_parsed,
    batch_insert_raw_materials,
    update_raw_material,
    search_raw_materials,
    fetch_all_formula_ingredients,
    fetch_formula_ingredients_with_regulatory,
    fetch_regulatory_db_counts,
    fetch_ingredient_breakdown,
)
from backend.compliance import check_formula as compliance_check_formula
from backend.models import (
    ScrapeRequest, ScrapeResult, FormulaCreate,
    MaterialCreate, MaterialPatch, ComplianceCheckRequest,
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = DATA_DIR / 'results'
BULK_JOBS_DIR = DATA_DIR / 'bulk_jobs'
JOBS_FILE = DATA_DIR / 'jobs.json'
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BULK_JOBS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title='Cosmetic P&D - Scraper API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

JOBS: Dict[str, Dict] = {}


def load_jobs():
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE, 'r', encoding='utf-8') as f:
                JOBS.update(json.load(f))
        except Exception:
            pass


def persist_jobs():
    with open(JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(JOBS, f, ensure_ascii=False, indent=2)


@app.on_event('startup')
async def startup():
    load_jobs()


# ------------------------------------------------------------------
# API Routes
# ------------------------------------------------------------------

@app.get('/api/stats')
async def api_stats():
    return await fetch_stats()


@app.get('/api/materials')
async def api_materials():
    return await fetch_raw_materials()


@app.get('/api/materials/search')
async def api_materials_search(q: str = '', limit: int = 20):
    if len(q.strip()) < 2:
        return []
    return await search_raw_materials(q.strip(), min(limit, 30))


@app.post('/api/materials', status_code=201)
async def api_create_material(data: MaterialCreate):
    try:
        return await create_raw_material(data.model_dump(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch('/api/materials/{material_id}')
async def api_update_material(material_id: str, data: MaterialPatch):
    patch = data.model_dump(exclude_none=True)
    if not patch:
        raise HTTPException(status_code=400, detail='No fields to update')
    result = await update_raw_material(material_id, patch)
    if result is None:
        raise HTTPException(status_code=404, detail='Material not found or update failed')
    return result


@app.post('/api/compliance/check')
async def api_compliance_check(data: ComplianceCheckRequest):
    findings = compliance_check_formula([i.model_dump() for i in data.ingredients])
    return {
        'findings': findings,
        'has_banned':    any(f['level'] == 'banned' for f in findings),
        'has_violation': any(f['exceeded'] for f in findings),
        'total': len(findings),
    }


@app.get('/api/compliance/db')
async def api_compliance_db():
    from backend.compliance import REGULATORY
    return [
        {'inci_name': k, **v}
        for k, v in REGULATORY.items()
    ]


@app.get('/api/compliance/summary')
async def api_compliance_summary():
    """Regulatory dashboard: live DB counts + per-formula violation scan.

    Priority: uses raw_materials.regulatory_status / max_limit_pct / regulatory_notes
    columns (populated by activate_regulatory.py).  Falls back to the static
    Python REGULATORY dict when those columns are not yet migrated.
    """
    from backend.compliance import REGULATORY, check_formula
    from collections import defaultdict

    # ── 1. Live DB counts (three parallel HEAD requests, fast) ────────────────
    db_counts = await fetch_regulatory_db_counts()
    use_db = db_counts['total'] > 0   # False → columns not yet migrated

    if use_db:
        db_banned    = db_counts['prohibited']
        db_restricted = db_counts['restricted']
        db_warning   = db_counts['with_notes']
        db_total     = db_counts['total']
        data_source  = 'database'
    else:
        db_banned    = sum(1 for v in REGULATORY.values() if v.get('level') == 'banned')
        db_restricted = sum(1 for v in REGULATORY.values() if v.get('level') == 'restricted')
        db_warning   = sum(1 for v in REGULATORY.values()
                          if 'คำเตือน' in v.get('notes', '') or 'ฉลาก' in v.get('notes', ''))
        db_total     = len(REGULATORY)
        data_source  = 'static'

    # ── 2. Formula violation scan ─────────────────────────────────────────────
    formula_violations: List[Dict] = []
    formulas_checked   = 0
    total_violations   = 0

    try:
        if use_db:
            rows = await fetch_formula_ingredients_with_regulatory()
        else:
            rows = await fetch_all_formula_ingredients()

        by_formula: Dict[str, List] = defaultdict(list)
        for row in rows:
            rm = row.get('raw_materials') or {}
            entry: Dict = {
                'inci_name':  rm.get('inci_name', ''),
                'trade_name': rm.get('trade_name', ''),
                'percentage': row.get('percentage', 0),
            }
            if use_db:
                entry['regulatory_status'] = rm.get('regulatory_status')
                entry['max_limit_pct']     = rm.get('max_limit_pct')
                entry['regulatory_notes']  = rm.get('regulatory_notes')
            by_formula[row['formula_id']].append(entry)

        formulas_checked = len(by_formula)

        for fid, ings in by_formula.items():
            findings: List[Dict] = []

            if use_db:
                # DB-column scan: prohibited → banned; restricted > max → exceeded
                for ing in ings:
                    status = ing.get('regulatory_status')
                    if not status:
                        continue
                    pct      = float(ing.get('percentage') or 0)
                    raw_max  = ing.get('max_limit_pct')
                    max_pct  = float(raw_max) if raw_max is not None else None
                    exceeded = (status == 'prohibited') or (max_pct is not None and pct > max_pct)
                    findings.append({
                        'inci_name':     ing['inci_name'],
                        'trade_name':    ing['trade_name'],
                        'percentage':    pct,
                        'level':         'banned' if status == 'prohibited' else 'restricted',
                        'exceeded':      exceeded,
                        'max_limit_pct': max_pct,
                        'notes':         ing.get('regulatory_notes') or '',
                    })
            else:
                findings = check_formula(ings)

            if findings:
                total_violations += len(findings)
                formula_violations.append({
                    'formula_id':   fid,
                    'violations':   len(findings),
                    'has_banned':   any(f['level'] == 'banned'   for f in findings),
                    'has_exceeded': any(f.get('exceeded')        for f in findings),
                    'details':      findings[:10],   # up to 10 ingredient-level rows per formula
                })
    except Exception:
        pass

    return {
        'regulatory_db': {
            'banned':           db_banned,
            'restricted':       db_restricted,
            'warning_required': db_warning,
            'total':            db_total,
            'source':           data_source,
        },
        'formula_stats': {
            'checked':          formulas_checked,
            'with_violations':  len(formula_violations),
            'total_violations': total_violations,
        },
        'formula_violations': formula_violations,
    }


@app.get('/api/dashboard/ingredient-breakdown')
async def api_ingredient_breakdown():
    """Return ingredient counts grouped into 6 functional categories."""
    try:
        return await fetch_ingredient_breakdown()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get('/api/formulas')
async def api_formulas():
    return await fetch_formulas()


@app.get('/api/scrape-results')
async def api_scrape_results(limit: int = 20):
    return await fetch_scrape_results(limit=limit)


@app.post('/api/formulas', status_code=201)
async def api_create_formula(data: FormulaCreate):
    try:
        formula = await create_formula({
            'formula_code': data.formula_code,
            'product_name': data.product_name,
            'target_skin_type': data.target_skin_type,
            'batch_size_g': data.batch_size_g,
            'loss_percentage': data.loss_percentage,
            'status': 'draft',
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    formula_id = formula['id']
    for ing in data.ingredients:
        await create_formula_ingredient({
            'formula_id': formula_id,
            'material_id': ing.material_id,
            'phase': ing.phase,
            'percentage': ing.percentage,
        })
    return formula


@app.get('/api/formulas/{formula_id}')
async def api_get_formula(formula_id: str):
    result = await fetch_formula_with_ingredients(formula_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Formula not found')
    return result


def _build_material_rows(
    parsed: List[Dict],
    source_url: str,
    existing_set: Set[str],
    seen: Set[str],
) -> List[Dict]:
    rows: List[Dict] = []
    for ing in parsed:
        name = (ing.get('name') or '').strip()
        if len(name) < 3:
            continue
        key = name.lower()
        if key in existing_set or key in seen:
            continue
        seen.add(key)
        rows.append({
            'trade_name': name,
            'inci_name': name,
            'supplier': source_url or None,
            'is_active': True,
        })
    return rows


@app.post('/api/sync-materials')
async def api_sync_materials():
    try:
        scrape_rows = await fetch_all_scrape_parsed()
        existing = await fetch_all_inci_names()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'DB fetch error: {e}')

    existing_set: Set[str] = set(existing)
    seen: Set[str] = set()
    to_insert: List[Dict] = []

    for row in scrape_rows:
        parsed = row.get('parsed') or []
        job = row.get('scrape_jobs') or {}
        source_url = job.get('source_url', '') if isinstance(job, dict) else ''
        to_insert.extend(_build_material_rows(parsed, source_url, existing_set, seen))

    try:
        inserted = await batch_insert_raw_materials(to_insert)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'DB insert error: {e}')

    return {'inserted': inserted, 'total_candidates': len(to_insert)}


@app.post('/api/scrape/bulk')
async def api_bulk_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    bulk_job_id = str(uuid4())
    progress_path = BULK_JOBS_DIR / f'{bulk_job_id}.json'
    # Write initial state so polling can start immediately
    progress_path.write_text(json.dumps({
        'status': 'discovering',
        'category_url': str(req.url),
        'total': 0, 'done': 0, 'failed': 0,
        'materials_added': 0, 'current_url': '', 'error': '',
    }, ensure_ascii=False), encoding='utf-8')
    background_tasks.add_task(run_bulk_scrape, bulk_job_id, str(req.url))
    return {'bulk_job_id': bulk_job_id}


@app.get('/api/scrape/bulk/{bulk_job_id}')
async def api_bulk_status(bulk_job_id: str):
    progress_path = BULK_JOBS_DIR / f'{bulk_job_id}.json'
    if not progress_path.exists():
        raise HTTPException(
            status_code=404,
            detail='Bulk job not found (server may have restarted)',
        )
    return json.loads(progress_path.read_text(encoding='utf-8'))


@app.post('/scrape')
async def enqueue_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    JOBS[job_id] = {'status': 'pending', 'url': str(req.url)}
    persist_jobs()
    remote_job = await create_scrape_job(str(req.url))
    if remote_job and isinstance(remote_job, dict) and remote_job.get('id'):
        JOBS[job_id]['remote_job_id'] = remote_job['id']
        persist_jobs()

    background_tasks.add_task(run_scrape, job_id, str(req.url))
    return {'job_id': job_id}


@app.get('/scrape/{job_id}')
async def get_scrape(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    result_path = RESULTS_DIR / f"{job_id}.json"
    result = None
    if result_path.exists():
        with open(result_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
    return {'job': job, 'result': result}


# ------------------------------------------------------------------
# AI — Trade Name → INCI
# ------------------------------------------------------------------

GEMINI_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

async def _gemini_text(prompt: str) -> str:
    """Call Gemini and return raw text."""
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Gemini error {r.status_code}: {r.text[:200]}")
    return r.json()['candidates'][0]['content']['parts'][0]['text'].strip()

async def _gemini_trade_to_inci(trade_name: str) -> dict:
    prompt = (
        "You are a cosmetic ingredient expert. "
        "Convert the trade name below to its INCI name.\n\n"
        f"Trade name: {trade_name}\n\n"
        "Reply ONLY with valid JSON, no markdown fences:\n"
        '{"inci_name":"...","confidence":"high|medium|low","notes":"brief reason"}'
    )
    raw = await _gemini_text(prompt)
    raw = raw.replace('```json', '').replace('```', '').strip()
    return json.loads(raw)


@app.post('/api/ai/trade-to-inci')
async def trade_to_inci(body: dict):
    trade_name = (body.get('trade_name') or '').strip()
    if not trade_name:
        raise HTTPException(400, 'trade_name is required')

    # 1. Try DB first (free, instant)
    db_results = await search_raw_materials(trade_name, limit=5)
    for r in db_results:
        tn = (r.get('trade_name') or '').lower()
        if tn and trade_name.lower() in tn or tn in trade_name.lower():
            if r.get('inci_name'):
                return {
                    'inci_name':  r['inci_name'],
                    'source':     'db',
                    'confidence': 'high',
                    'notes':      f"พบใน database: {r['trade_name']}",
                }

    # 2. Fallback to Gemini
    if not GEMINI_KEY:
        raise HTTPException(503, 'GEMINI_API_KEY not configured')
    result = await _gemini_trade_to_inci(trade_name)
    result['source'] = 'ai'
    return result


# ------------------------------------------------------------------
# Trends — Google News RSS + Gemini summary
# ------------------------------------------------------------------

_NEWS_QUERIES = [
    ('cosmetic ingredient trends 2025',   'Ingredient Trends'),
    ('skincare beauty innovation',        'Innovation'),
    ('cosmetic regulation safety update', 'Regulation'),
    ('natural organic beauty trends',     'Natural & Organic'),
]

@app.get('/api/trends/news')
async def get_trends_news():
    articles, seen = [], set()
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; newsbot/1.0)'}
    async with httpx.AsyncClient(timeout=15, headers=headers) as c:
        for query, category in _NEWS_QUERIES:
            url = (f"https://news.google.com/rss/search"
                   f"?q={url_quote(query)}&hl=en&gl=US&ceid=US:en")
            try:
                r = await c.get(url)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                for item in root.findall('.//item')[:5]:
                    title = item.findtext('title', '').strip()
                    # Google News appends " - Source" to title — strip it
                    if ' - ' in title:
                        title, src_from_title = title.rsplit(' - ', 1)
                    else:
                        src_from_title = ''
                    if title in seen:
                        continue
                    seen.add(title)
                    source_el = item.find('source')
                    pub = item.findtext('pubDate', '')[:16]
                    articles.append({
                        'title':    title.strip(),
                        'link':     item.findtext('link', ''),
                        'pubDate':  pub,
                        'source':   (source_el.text if source_el is not None
                                     else src_from_title),
                        'category': category,
                    })
            except Exception:
                continue
    return articles[:20]


@app.post('/api/trends/summary')
async def get_trends_summary(body: dict):
    headlines = body.get('headlines', [])
    if not headlines:
        raise HTTPException(400, 'headlines required')
    if not GEMINI_KEY:
        raise HTTPException(503, 'GEMINI_API_KEY not configured')
    prompt = (
        "คุณเป็นผู้เชี่ยวชาญด้านอุตสาหกรรมเครื่องสำอางและการพัฒนาสูตร\n\n"
        "จากข่าวสารเหล่านี้:\n" +
        "\n".join(f"• {h}" for h in headlines[:20]) +
        "\n\nกรุณาวิเคราะห์และสรุปเป็นภาษาไทย โดยแบ่งเป็น 3 หัวข้อดังนี้:\n\n"
        "**1. เทรนด์หลักที่น่าจับตา**\n"
        "สรุปเทรนด์ 3-4 ข้อที่สำคัญที่สุดสำหรับนักพัฒนาสูตรเครื่องสำอาง\n\n"
        "**2. วัตถุดิบ/ส่วนผสมที่กำลังมาแรง**\n"
        "ระบุชื่อวัตถุดิบหรือส่วนผสมที่ถูกพูดถึง พร้อมเหตุผล\n\n"
        "**3. ข้อแนะนำเชิงปฏิบัติ**\n"
        "แนะนำ 2-3 ข้อที่ทีม R&D ควรนำไปพิจารณาในการพัฒนาผลิตภัณฑ์\n\n"
        "ตอบกระชับ ชัดเจน ใช้ bullet points"
    )
    text = await _gemini_text(prompt)
    return {'summary': text}


# ------------------------------------------------------------------
# Frontend
# ------------------------------------------------------------------

@app.get('/')
async def serve_frontend():
    index = FRONTEND_DIR / 'index.html'
    if not index.exists():
        return {'message': 'Frontend not built yet. Run from project root.'}
    return FileResponse(index)

if FRONTEND_DIR.exists():
    app.mount('/frontend', StaticFiles(directory=FRONTEND_DIR), name='frontend')


# ------------------------------------------------------------------
# Background tasks  (multiprocessing — each gets a fresh OS process
# whose main thread has a clean ProactorEventLoop on Windows, fully
# compatible with Playwright subprocess spawning)
# ------------------------------------------------------------------

def _join_with_timeout(proc: multiprocessing.Process, timeout: int) -> None:
    """Block until proc exits or timeout (seconds) elapses, then kill."""
    proc.join(timeout=timeout)
    if proc.is_alive():
        print(f'[scrape] Process {proc.pid} exceeded timeout — terminating', flush=True)
        proc.terminate()
        proc.join(timeout=10)


async def run_scrape(job_id: str, url: str):
    from backend.scrape_workers import single_scrape_worker

    JOBS[job_id]['status'] = 'running'
    persist_jobs()

    result_path = str(RESULTS_DIR / f'{job_id}_worker.json')
    proc = multiprocessing.Process(
        target=single_scrape_worker,
        args=(url, result_path),
        daemon=True,
    )
    proc.start()
    await asyncio.get_running_loop().run_in_executor(
        None, _join_with_timeout, proc, 120
    )

    worker_result_file = Path(result_path)
    if not worker_result_file.exists():
        error_msg = 'Worker process produced no output (crash or timeout)'
        print(f'[run_scrape] job={job_id}: {error_msg}', flush=True)
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['error'] = error_msg
        remote_job_id = JOBS[job_id].get('remote_job_id')
        if remote_job_id:
            await update_scrape_job_status(remote_job_id, 'failed', error_msg)
        persist_jobs()
        return

    try:
        worker_result = json.loads(worker_result_file.read_text(encoding='utf-8'))
        worker_result_file.unlink(missing_ok=True)
    except Exception as e:
        error_msg = f'Failed to read worker result: {e}'
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['error'] = error_msg
        persist_jobs()
        return

    if not worker_result.get('ok'):
        error_msg = worker_result.get('tb', 'Unknown error in worker process')
        print(f'[run_scrape PROCESS ERROR] job={job_id}\n{error_msg}', flush=True)
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['error'] = error_msg
        remote_job_id = JOBS[job_id].get('remote_job_id')
        if remote_job_id:
            await update_scrape_job_status(remote_job_id, 'failed', 'Scraper process failed')
        persist_jobs()
        return

    try:
        res = worker_result['res']
        out = {
            'job_id': job_id,
            'url': url,
            'raw_html': res.get('raw_html'),
            'parsed': res.get('parsed', []),
            'errors': res.get('errors', []),
        }
        with open(RESULTS_DIR / f'{job_id}.json', 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        JOBS[job_id]['status'] = 'success'
        JOBS[job_id]['result_path'] = str(RESULTS_DIR / f'{job_id}.json')

        remote_job_id = JOBS[job_id].get('remote_job_id')
        if remote_job_id:
            await update_scrape_job_status(remote_job_id, 'success')
            await insert_scrape_result(remote_job_id, out['raw_html'], out['parsed'], out['errors'])

        # Auto-sync new INCI names into raw_materials (non-fatal)
        try:
            existing = await fetch_all_inci_names()
            new_rows = _build_material_rows(out['parsed'], url, set(existing), set())
            if new_rows:
                await batch_insert_raw_materials(new_rows)
        except Exception:
            pass

    except Exception as e:
        full_tb = traceback.format_exc()
        error_msg = f"{type(e).__name__}: {e}\n{full_tb}" if str(e) else full_tb
        print(f'[run_scrape POST-SCRAPE ERROR] job={job_id}\n{error_msg}', flush=True)
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['error'] = error_msg
        remote_job_id = JOBS[job_id].get('remote_job_id')
        if remote_job_id:
            await update_scrape_job_status(remote_job_id, 'failed', str(e))

    persist_jobs()


async def run_bulk_scrape(bulk_job_id: str, category_url: str):
    from backend.scrape_workers import bulk_scrape_worker

    progress_path = str(BULK_JOBS_DIR / f'{bulk_job_id}.json')
    proc = multiprocessing.Process(
        target=bulk_scrape_worker,
        args=(category_url, progress_path),
        daemon=True,
    )
    proc.start()
    # Wait up to 1 hour; _join_with_timeout kills if exceeded
    await asyncio.get_running_loop().run_in_executor(
        None, _join_with_timeout, proc, 3600
    )


if __name__ == '__main__':
    import uvicorn
    multiprocessing.freeze_support()   # required for Windows frozen executables
    uvicorn.run('backend.main:app', host='127.0.0.1', port=8000, reload=True)
