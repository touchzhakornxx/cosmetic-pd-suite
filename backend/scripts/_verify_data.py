import asyncio, os, sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

URL = os.getenv('SUPABASE_URL', '').rstrip('/')
KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')

async def main():
    h = {'apikey': KEY, 'Authorization': f'Bearer {KEY}', 'Prefer': 'count=exact'}
    async with httpx.AsyncClient(timeout=15) as c:
        # Exact count
        r = await c.get(f"{URL}/rest/v1/raw_materials?select=id&limit=0", headers=h)
        total = r.headers.get('content-range', '*/0').split('/')[-1]
        print(f"Exact row count: {total}")

        # Sample of OBF-sourced rows (supplier = function category)
        r2 = await c.get(
            f"{URL}/rest/v1/raw_materials?select=trade_name,supplier&order=created_at.desc&limit=10",
            headers={k: v for k, v in h.items() if k != 'Prefer'},
        )
        print("\nMost recently inserted rows:")
        for row in r2.json():
            print(f"  {row['trade_name'][:50]:<50} | {row['supplier']}")

        # Count by category sample
        r3 = await c.get(
            f"{URL}/rest/v1/raw_materials?supplier=eq.Skin+Conditioning&select=id&limit=0",
            headers=h,
        )
        sc = r3.headers.get('content-range', '*/0').split('/')[-1]
        print(f"\nRows with supplier='Skin Conditioning': {sc}")

asyncio.run(main())
