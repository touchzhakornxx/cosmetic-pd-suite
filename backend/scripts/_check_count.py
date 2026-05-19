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
    headers = {
        'apikey': KEY, 'Authorization': f'Bearer {KEY}',
        'Prefer': 'count=exact',
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{URL}/rest/v1/raw_materials?select=id&limit=0", headers=headers)
    cr = r.headers.get('content-range', '?')
    print(f"HTTP {r.status_code}  content-range: {cr}")
    print(f"Total rows in raw_materials: {cr.split('/')[-1]}")

asyncio.run(main())
