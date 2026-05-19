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
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.delete(
            f"{URL}/rest/v1/raw_materials?trade_name=like.DEBUG*",
            headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}',
                     'Prefer': 'return=minimal'},
        )
        print(f"Cleanup: {r.status_code}")

asyncio.run(main())
