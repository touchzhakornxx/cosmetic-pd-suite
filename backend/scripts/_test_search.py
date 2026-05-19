"""Quick smoke test for the search endpoint."""
import asyncio, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from backend.db import search_raw_materials

TESTS = [
    ('glyc',    'partial match for Glycerin / Glycerine / Glycerol'),
    ('glycerin','exact word match'),
    ('56-81-5', 'CAS number lookup for Glycerin'),
    ('niacin',  'partial match for Niacinamide'),
    ('arbutin', 'partial match for Alpha-Arbutin / Beta-Arbutin'),
    ('zinc',    'partial match for Zinc Oxide'),
    ('XYZ_NOTEXIST', 'should return 0 results'),
]

async def main():
    print(f'{"Query":<20} {"Expect":<45} {"Hits":>4}  First result')
    print('-' * 100)
    for q, desc in TESTS:
        rows = await search_raw_materials(q, limit=5)
        first = rows[0]['trade_name'] if rows else '—'
        print(f'{q:<20} {desc:<45} {len(rows):>4}  {first}')

asyncio.run(main())
