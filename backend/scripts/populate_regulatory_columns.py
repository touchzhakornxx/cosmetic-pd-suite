"""
populate_regulatory_columns.py
================================
Sync regulatory_status, max_limit_pct, and regulatory_notes from the
built-in REGULATORY dict (backend/compliance.py) into the raw_materials
table in Supabase.

Run AFTER executing regulatory_columns_migration.sql in the SQL Editor:
    python -m backend.scripts.populate_regulatory_columns
"""
import asyncio, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

import httpx

URL = os.getenv('SUPABASE_URL', '').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
REST = f"{URL}/rest/v1"
H = {
    'apikey': KEY, 'Authorization': f'Bearer {KEY}',
    'Content-Type': 'application/json', 'Prefer': 'return=minimal',
}

async def patch_material(inci_upper: str, payload: dict):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.patch(
            f"{REST}/raw_materials",
            params={'inci_name': f'eq.{inci_upper}'},
            json=payload,
            headers=H,
        )
    return r.status_code, inci_upper

async def main():
    from backend.compliance import REGULATORY

    STATUS_MAP = {'banned': 'prohibited', 'restricted': 'restricted'}
    tasks = []
    for inci_upper, entry in REGULATORY.items():
        level   = entry.get('level', '')
        status  = STATUS_MAP.get(level)
        if not status:
            continue
        payload = {'regulatory_status': status}
        if entry.get('max_pct') is not None:
            payload['max_limit_pct'] = entry['max_pct']
        if entry.get('notes'):
            payload['regulatory_notes'] = entry['notes']
        tasks.append(patch_material(inci_upper, payload))

    print(f"Updating {len(tasks)} ingredients...")
    results = await asyncio.gather(*tasks)
    ok  = sum(1 for code, _ in results if code in (200, 201, 204))
    err = [(code, name) for code, name in results if code not in (200, 201, 204)]
    print(f"Updated: {ok}  Errors: {len(err)}")
    for code, name in err:
        print(f"  HTTP {code}: {name}")

if __name__ == '__main__':
    asyncio.run(main())
