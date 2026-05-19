"""One-shot: insert a single OBF row and print the full Supabase error."""
import asyncio, json, os, sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

URL = os.getenv('SUPABASE_URL', '').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')

async def main():
    # First: fetch table columns to understand schema
    print("=== Table columns (via /rest/v1/raw_materials?limit=1) ===")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{URL}/rest/v1/raw_materials?limit=1",
                        headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}'})
        print(f"Status: {r.status_code}")
        rows = r.json()
        if rows:
            print("Columns:", list(rows[0].keys()))
        else:
            print("No rows returned (empty table or RLS blocking)")

    # Second: attempt single-row insert with minimal data (only trade_name + inci_name)
    print("\n=== Test insert: only trade_name + inci_name ===")
    test_row = {'trade_name': 'DEBUG TEST INGREDIENT', 'inci_name': 'DEBUG TEST INGREDIENT'}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{URL}/rest/v1/raw_materials",
                         json=[test_row],
                         headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}',
                                  'Content-Type': 'application/json',
                                  'Prefer': 'return=representation'})
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:1000]}")

    # Third: try with all known columns
    print("\n=== Test insert: all known columns ===")
    full_row = {
        'trade_name': 'DEBUG TEST INGREDIENT 2',
        'inci_name':  'DEBUG TEST INGREDIENT 2',
        'supplier':   'Skin Conditioning',
        'cas_number':  None,
        'price_per_kg': None,
        'is_active':   True,
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{URL}/rest/v1/raw_materials",
                         json=[full_row],
                         headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}',
                                  'Content-Type': 'application/json',
                                  'Prefer': 'return=representation'})
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:2000]}")

asyncio.run(main())
