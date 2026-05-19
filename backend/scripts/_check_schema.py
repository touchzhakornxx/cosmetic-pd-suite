"""Check raw_materials actual schema and test search filters individually."""
import asyncio, os, sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

URL = os.getenv('SUPABASE_URL', '').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
REST = f"{URL}/rest/v1"
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}

async def get(path, params=None):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{REST}{path}", params=params, headers=H)
    return r.status_code, r.json()

async def main():
    # 1. Exact columns
    code, rows = await get('/raw_materials', {'limit': '1'})
    if rows:
        print("Columns:", list(rows[0].keys()))
    else:
        print("No rows returned")

    # 2. Test each filter individually
    tests = [
        ('trade_name',    'ilike.*glycerin*'),
        ('inci_name',     'ilike.*glycerin*'),
        ('cas_number',    'ilike.*56-81*'),   # does this column exist?
        ('cas',           'ilike.*56-81*'),   # alternative name?
        ('cas_no',        'ilike.*56-81*'),   # alternative name?
    ]
    print()
    for col, flt in tests:
        code, data = await get('/raw_materials', {
            col: flt, 'select': 'id,trade_name', 'limit': '3'
        })
        if code == 200:
            names = [r['trade_name'] for r in data]
            print(f"  {col}.{flt}  -> HTTP {code}  hits={len(data)}  {names}")
        else:
            err = data.get('message') or data.get('code') or str(data)[:120]
            print(f"  {col}.{flt}  -> HTTP {code}  ERROR: {err}")

    # 3. Test or() with all three candidate column names
    for cas_col in ('cas_number', 'cas', 'cas_no'):
        code, data = await get('/raw_materials', {
            'or': f'(trade_name.ilike.*glyc*,{cas_col}.ilike.*56-81*)',
            'select': 'id,trade_name',
            'limit': '3',
        })
        if code == 200:
            print(f"  or() with {cas_col}  -> OK  hits={len(data)}")
        else:
            err = data.get('message') or data.get('code') or str(data)[:120]
            print(f"  or() with {cas_col}  -> HTTP {code}  {err}")

asyncio.run(main())
