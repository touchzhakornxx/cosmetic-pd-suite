import asyncio
import os
import time as _time
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else None


class SupabaseError(Exception):
    pass


def _supabase_headers() -> Dict[str, str]:
    if not SUPABASE_URL:
        raise SupabaseError('SUPABASE_URL must be set in environment')

    api_key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not api_key:
        raise SupabaseError('SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set in environment')

    return {
        'apikey': api_key,
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }


async def _supabase_insert(table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not SUPABASE_REST_URL:
        raise SupabaseError('Supabase REST URL is not configured')
    url = f"{SUPABASE_REST_URL}/{table}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=[payload], headers=_supabase_headers())
        if resp.status_code not in (200, 201, 202):
            raise SupabaseError(f'Insert failed {resp.status_code}: {resp.text}')
        data = resp.json()
        return data[0] if isinstance(data, list) and data else data


async def _supabase_update(table: str, record_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not SUPABASE_REST_URL:
        raise SupabaseError('Supabase REST URL is not configured')
    url = f"{SUPABASE_REST_URL}/{table}?id=eq.{record_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.patch(url, json=payload, headers=_supabase_headers())
        if resp.status_code not in (200, 202):
            raise SupabaseError(f'Update failed {resp.status_code}: {resp.text}')
        data = resp.json()
        return data[0] if isinstance(data, list) and data else data


async def create_scrape_job(source_url: str) -> Optional[Dict[str, Any]]:
    try:
        return await _supabase_insert('scrape_jobs', {'source_url': source_url, 'status': 'pending'})
    except Exception:
        return None


async def update_scrape_job_status(job_id: str, status: str, error: Optional[str] = None) -> Optional[Dict[str, Any]]:
    payload = {'status': status}
    if error is not None:
        payload['error'] = error
    try:
        return await _supabase_update('scrape_jobs', job_id, payload)
    except Exception:
        return None


async def _supabase_select(table: str, query: str = '') -> List[Dict[str, Any]]:
    if not SUPABASE_REST_URL:
        raise SupabaseError('Supabase REST URL is not configured')
    url = f"{SUPABASE_REST_URL}/{table}"
    if query:
        url += f"?{query}"
    headers = {k: v for k, v in _supabase_headers().items() if k != 'Prefer'}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
    if resp.status_code != 200:
        raise SupabaseError(f'Select failed {resp.status_code}: {resp.text}')
    return resp.json()


async def _count_table(table: str) -> int:
    if not SUPABASE_REST_URL:
        return 0
    url = f"{SUPABASE_REST_URL}/{table}?select=id&limit=0"
    headers = {**{k: v for k, v in _supabase_headers().items() if k != 'Prefer'}, 'Prefer': 'count=exact'}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        cr = resp.headers.get('content-range', '*/0')
        total = cr.split('/')[-1]
        return int(total) if total.isdigit() else 0
    except Exception:
        return 0


async def fetch_raw_materials() -> List[Dict[str, Any]]:
    try:
        return await _supabase_select('raw_materials', 'order=created_at.desc')
    except Exception:
        return []


async def fetch_formulas() -> List[Dict[str, Any]]:
    try:
        return await _supabase_select('formulas', 'order=created_at.desc')
    except Exception:
        return []


async def fetch_scrape_results(limit: int = 20) -> List[Dict[str, Any]]:
    try:
        return await _supabase_select(
            'scrape_results',
            f'select=id,job_id,parsed,errors,created_at,scrape_jobs(source_url,status,created_at)'
            f'&order=created_at.desc&limit={limit}',
        )
    except Exception:
        return []


async def fetch_stats() -> Dict[str, int]:
    tables = ['raw_materials', 'formulas', 'scrape_jobs', 'scrape_results']
    counts = await asyncio.gather(*[_count_table(t) for t in tables], return_exceptions=True)
    return {t: (c if isinstance(c, int) else 0) for t, c in zip(tables, counts)}


async def insert_scrape_result(job_id: str, raw_html: Optional[str], parsed: Any, errors: Any) -> Optional[Dict[str, Any]]:
    try:
        return await _supabase_insert(
            'scrape_results',
            {
                'job_id': job_id,
                'raw_html': raw_html,
                'parsed': parsed,
                'errors': errors,
            },
        )
    except Exception:
        return None


async def create_formula(data: Dict[str, Any]) -> Dict[str, Any]:
    return await _supabase_insert('formulas', data)


async def create_formula_ingredient(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return await _supabase_insert('formula_ingredients', data)
    except Exception:
        return None


async def fetch_formula_with_ingredients(formula_id: str) -> Optional[Dict[str, Any]]:
    try:
        rows = await _supabase_select('formulas', f'id=eq.{formula_id}')
        if not rows:
            return None
        formula = rows[0]
        ings = await _supabase_select(
            'formula_ingredients',
            f'formula_id=eq.{formula_id}'
            f'&select=id,phase,percentage,material_id,raw_materials(trade_name,inci_name,price_per_kg)'
            f'&order=phase.asc,percentage.desc',
        )
        formula['ingredients'] = ings
        return formula
    except Exception:
        return None


async def create_raw_material(data: Dict[str, Any]) -> Dict[str, Any]:
    return await _supabase_insert('raw_materials', data)


async def update_raw_material(material_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return await _supabase_update('raw_materials', material_id, patch)
    except Exception:
        return None


async def search_raw_materials(q: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Case-insensitive partial-match search across trade_name, inci_name, and
    cas_number.

    PostgREST supports * as the ilike wildcard when the pattern is embedded
    directly in the URL query string (not via params= encoding, which can
    cause double-encoding issues with %).  We build the URL string ourselves
    so PostgREST sees the literal * characters it expects.

    Fallback: if the 3-column OR query fails (e.g. PostgREST schema cache
    issue), we retry with trade_name + inci_name only to avoid crashing.
    """
    import re
    if not SUPABASE_REST_URL:
        return []
    safe = re.sub(r'[,();\'\"\\*%]', '', q.strip())[:80]
    if not safe:
        return []

    headers = {k: v for k, v in _supabase_headers().items() if k != 'Prefer'}
    common = f"select=id,trade_name,inci_name,cas_number,price_per_kg,supplier&is_active=eq.true&order=trade_name.asc&limit={limit}"

    async def _get(or_clause: str):
        url = f"{SUPABASE_REST_URL}/raw_materials?or=({or_clause})&{common}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        return resp

    # Attempt 1: search all three fields (trade_name, inci_name, cas_number)
    try:
        triple = (
            f"trade_name.ilike.*{safe}*,"
            f"inci_name.ilike.*{safe}*,"
            f"cas_number.ilike.*{safe}*"
        )
        resp = await _get(triple)
        if resp.status_code == 200:
            return resp.json()
        print(f"[search] 3-column query failed ({resp.status_code}): {resp.text[:200]}", flush=True)
    except Exception as e:
        print(f"[search] 3-column query error: {e}", flush=True)

    # Attempt 2: fallback — trade_name and inci_name only
    try:
        double = f"trade_name.ilike.*{safe}*,inci_name.ilike.*{safe}*"
        resp = await _get(double)
        if resp.status_code == 200:
            return resp.json()
        print(f"[search] 2-column fallback failed ({resp.status_code}): {resp.text[:200]}", flush=True)
    except Exception as e:
        print(f"[search] 2-column fallback error: {e}", flush=True)

    return []


async def fetch_all_inci_names() -> List[str]:
    try:
        rows = await _supabase_select('raw_materials', 'select=inci_name')
        return [r['inci_name'].strip().lower() for r in rows if r.get('inci_name')]
    except Exception:
        return []


async def fetch_all_scrape_parsed() -> List[Dict[str, Any]]:
    try:
        return await _supabase_select(
            'scrape_results',
            'select=parsed,scrape_jobs(source_url)&order=created_at.desc',
        )
    except Exception:
        return []


async def fetch_all_formula_ingredients() -> List[Dict[str, Any]]:
    """Return every formula_ingredient row joined with its raw_material names.
    Used by the compliance summary to batch-check all saved formulas at once."""
    try:
        return await _supabase_select(
            'formula_ingredients',
            'select=formula_id,percentage,raw_materials(trade_name,inci_name)&order=formula_id',
        )
    except Exception:
        return []


async def fetch_formula_ingredients_with_regulatory() -> List[Dict[str, Any]]:
    """Like fetch_all_formula_ingredients but includes the live regulatory columns
    (regulatory_status, max_limit_pct, regulatory_notes) from raw_materials.
    Used when DB columns have been migrated and populated."""
    try:
        return await _supabase_select(
            'formula_ingredients',
            (
                'select=formula_id,percentage,'
                'raw_materials(trade_name,inci_name,'
                'regulatory_status,max_limit_pct,regulatory_notes)'
                '&order=formula_id'
            ),
        )
    except Exception:
        return []


async def fetch_regulatory_db_counts() -> Dict[str, int]:
    """Count raw_materials by regulatory_status using three parallel HEAD queries.
    Returns zero counts if the DB columns have not yet been migrated."""
    if not SUPABASE_REST_URL:
        return {'prohibited': 0, 'restricted': 0, 'with_notes': 0, 'total': 0}

    count_headers = {
        **{k: v for k, v in _supabase_headers().items() if k != 'Prefer'},
        'Prefer': 'count=exact',
    }

    async def _count(filter_q: str) -> int:
        url = f"{SUPABASE_REST_URL}/raw_materials?{filter_q}&select=id&limit=0"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=count_headers)
            cr = resp.headers.get('content-range', '*/0')
            total = cr.split('/')[-1]
            return int(total) if total.isdigit() else 0
        except Exception:
            return 0

    prohibited, restricted, with_notes = await asyncio.gather(
        _count('regulatory_status=eq.prohibited'),
        _count('regulatory_status=eq.restricted'),
        _count('regulatory_notes=not.is.null'),
    )
    return {
        'prohibited': prohibited,
        'restricted': restricted,
        'with_notes': with_notes,
        'total':      prohibited + restricted,
    }


_breakdown_cache: Optional[Dict[str, int]] = None
_breakdown_cache_ts: float = 0.0


async def fetch_ingredient_breakdown() -> Dict[str, int]:
    """
    Classify every active raw_material into 6 functional groups using the
    'supplier' column (which stores the INCI function category from seeding).

    Pagination uses page_size=1000 to respect Supabase's default max_rows cap —
    the loop continues until a page shorter than 1000 is returned (last page).
    Results cached 5 minutes in-process.
    """
    global _breakdown_cache, _breakdown_cache_ts
    if _breakdown_cache is not None and _time.time() - _breakdown_cache_ts < 300:
        return _breakdown_cache

    if not SUPABASE_REST_URL:
        return {}

    headers = {k: v for k, v in _supabase_headers().items() if k != 'Prefer'}
    rows: List[Dict[str, Any]] = []
    # Use 1000 — Supabase's default max_rows; asking for more silently caps there,
    # making len(batch) < page_size always true even when more rows remain.
    page_size = 1000
    offset = 0

    async with httpx.AsyncClient(timeout=120.0) as client:
        while True:
            url = (
                f"{SUPABASE_REST_URL}/raw_materials"
                f"?select=inci_name,supplier"
                f"&limit={page_size}&offset={offset}"
            )
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < page_size:
                break  # final page
            offset += page_size

    counts: Dict[str, int] = {
        'Actives & Extracts':        0,
        'Emulsifiers & Surfactants': 0,
        'Thickeners & Polymers':     0,
        'Solvents & Bases':          0,
        'Preservatives':             0,
        'Others':                    0,
    }

    def _classify(inci: str, cat: str) -> str:
        # Both fields lowercased once — all comparisons are case-insensitive
        c = (cat or '').lower()
        n = (inci or '').lower()

        # ── 1. Preservatives ─────────────────────────────────────────────────
        if ('preserv' in c or 'antimicrob' in c or 'antifung' in c or
                'antibact' in c or 'antidandr' in c or
                'paraben' in n):
            return 'Preservatives'

        # ── 2. Emulsifiers & Surfactants ──────────────────────────────────────
        if ('emulsif' in c or 'surfactant' in c or 'cleansing' in c or
                'detergent' in c or 'foaming' in c or 'wetting' in c or
                'solubilizer' in c or 'emulsion stabil' in c or
                'defoaming' in c or 'opacif' in c):
            return 'Emulsifiers & Surfactants'

        # ── 3. Thickeners & Polymers ──────────────────────────────────────────
        if ('thicken' in c or 'gelling' in c or 'viscosit' in c or
                'film form' in c or 'polymer' in c or 'binding' in c or
                'bulking' in c or 'hair fix' in c or 'plasticiz' in c or
                'slip modif' in c or
                'carbomer' in n or 'cellulose' in n or 'hyaluronate' in n):
            return 'Thickeners & Polymers'

        # ── 4. Actives & Extracts ─────────────────────────────────────────────
        # Broad: conditioning/moisturising/emollient actives + botanicals + UV
        if ('skin condition' in c or 'hair condition' in c or
                'condition' in c or 'emollient' in c or
                'humectant' in c or 'moisturis' in c or 'moisturiz' in c or
                'active' in c or 'extract' in c or
                'antioxidant' in c or 'whitening' in c or
                'botanical' in c or 'ferment' in c or 'probiotic' in c or
                'exfoliant' in c or 'keratolytic' in c or 'abrasiv' in c or
                'uv filter' in c or 'uv absorber' in c or 'sunscreen' in c or
                'soothing' in c or 'tonic' in c or
                'amino acid' in c or 'anti-aging' in c or 'antiaging' in c or
                'biotech' in c or 'protein' in c or 'peptide' in c or
                'vitamin' in c or 'chelat' in c or
                'bleach' in c or 'oxidiz' in c or 'reducing' in c or
                'antistatic' in c or 'masking' in c):
            return 'Actives & Extracts'

        # ── 5. Solvents & Bases ───────────────────────────────────────────────
        if ('solvent' in c or 'buffering' in c or 'ph adjuster' in c or
                'ph buffer' in c or 'propellant' in c or 'denaturant' in c or
                'diluent' in c or 'carrier' in c or
                n in ('aqua', 'water', 'alcohol denat.') or
                n.startswith('aqua') or
                'glycol' in n or
                ('alcohol' in n and 'fatty' not in c and 'cetyl' not in n
                 and 'stearyl' not in n and 'cetearyl' not in n)):
            return 'Solvents & Bases'

        # ── 6. Others — fragrance, colorant, mineral, wax, generic etc. ───────
        return 'Others'

    for row in rows:
        bucket = _classify(row.get('inci_name') or '', row.get('supplier') or '')
        counts[bucket] += 1

    _breakdown_cache = counts
    _breakdown_cache_ts = _time.time()
    return counts


async def batch_insert_raw_materials(items: List[Dict[str, Any]]) -> int:
    if not items or not SUPABASE_REST_URL:
        return 0
    url = f"{SUPABASE_REST_URL}/raw_materials"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=items, headers=_supabase_headers())
    if resp.status_code not in (200, 201, 202):
        raise SupabaseError(f'Batch insert failed {resp.status_code}: {resp.text}')
    data = resp.json()
    return len(data) if isinstance(data, list) else 0
