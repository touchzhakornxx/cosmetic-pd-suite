"""
Subprocess worker functions for Playwright-based scraping.

These are TOP-LEVEL functions so they are picklable by multiprocessing on
Windows (spawn start-method).  Each worker runs in a fresh OS process.

IMPORTANT — policy must be set before ANY Playwright import:
On Windows, importing playwright.sync_api can latch a SelectorEventLoop onto
the thread via asyncio internals, which raises NotImplementedError when
Playwright later tries to spawn the browser subprocess (subprocess_exec is
only supported by ProactorEventLoop).  Setting WindowsProactorEventLoopPolicy
first guarantees every event loop created in this process uses ProactorEventLoop.

Results / progress are communicated back to the parent FastAPI process via
JSON files rather than shared memory (safe across process boundaries).
"""
import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Set


def _ensure_proactor() -> None:
    """Must be called before any Playwright import on Windows."""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# ── helpers ──────────────────────────────────────────────────────────────────

def _write(path: str, data: Dict) -> None:
    try:
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def _build_rows(
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


# ── single-product worker ────────────────────────────────────────────────────

def single_scrape_worker(url: str, result_path: str) -> None:
    """
    Scrape one product URL and write the outcome to result_path:
      {'ok': True,  'res': {raw_html, parsed, errors}}
      {'ok': False, 'tb':  '<traceback string>'}
    """
    # Set ProactorEventLoop policy BEFORE importing Playwright
    _ensure_proactor()

    from backend.scrapers.myskinrecipes import MySkinRecipesScraper
    try:
        res = MySkinRecipesScraper().scrape(url)
        _write(result_path, {'ok': True, 'res': res})
    except Exception:
        _write(result_path, {'ok': False, 'tb': traceback.format_exc()})


# ── bulk-category worker ─────────────────────────────────────────────────────

def bulk_scrape_worker(category_url: str, progress_path: str) -> None:
    """
    Discover every product URL in a MySkinRecipes category, scrape each one,
    and auto-insert new INCI names into raw_materials via Supabase.

    Progress is written to progress_path after every step so the parent
    FastAPI process can serve it via the polling endpoint without any IPC.
    """
    # Set ProactorEventLoop policy BEFORE importing Playwright
    _ensure_proactor()

    from backend.scrapers.myskinrecipes import scrape_category_links, MySkinRecipesScraper
    from backend.db import fetch_all_inci_names, batch_insert_raw_materials

    job: Dict[str, Any] = {
        'status': 'discovering',
        'category_url': category_url,
        'total': 0,
        'done': 0,
        'failed': 0,
        'materials_added': 0,
        'current_url': '',
        'error': '',
    }
    _write(progress_path, job)

    # ── Step 1: discover all product links ───────────────────────────────────
    try:
        product_urls = scrape_category_links(category_url)
    except Exception:
        job['status'] = 'failed'
        job['error'] = traceback.format_exc()
        _write(progress_path, job)
        return

    if not product_urls:
        job['status'] = 'failed'
        job['error'] = 'ไม่พบสินค้าในหน้าหมวดหมู่ กรุณาตรวจสอบ URL'
        _write(progress_path, job)
        return

    job['total'] = len(product_urls)
    job['status'] = 'scraping'
    _write(progress_path, job)

    # ── Step 2: load existing INCI names (asyncio.run is fine on subprocess main thread) ──
    try:
        existing_set: Set[str] = set(asyncio.run(fetch_all_inci_names()))
    except Exception:
        existing_set = set()

    # ── Step 3: scrape each product sequentially ─────────────────────────────
    for prod_url in product_urls:
        job['current_url'] = prod_url
        _write(progress_path, job)

        try:
            result = MySkinRecipesScraper().scrape(prod_url)
            parsed = result.get('parsed', [])
            new_rows = _build_rows(parsed, prod_url, existing_set, set())
            if new_rows:
                asyncio.run(batch_insert_raw_materials(new_rows))
                for row in new_rows:
                    existing_set.add(row['inci_name'].lower())
                job['materials_added'] += len(new_rows)
            job['done'] += 1
        except Exception:
            print(
                f'[bulk_scrape_worker] FAILED {prod_url}\n{traceback.format_exc()}',
                flush=True,
            )
            job['failed'] += 1

        _write(progress_path, job)

    job['status'] = 'done'
    _write(progress_path, job)
    print(
        f'[bulk_scrape_worker] Done -- '
        f'done={job["done"]} failed={job["failed"]} added={job["materials_added"]}',
        flush=True,
    )
