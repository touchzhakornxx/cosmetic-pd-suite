import asyncio, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
from backend.db import search_raw_materials

def rerank(rows, q):
    ql = q.lower()
    def rank(m):
        t = (m['trade_name'] or '').lower()
        n = (m['inci_name']  or '').lower()
        if t == ql or n == ql:              return 0
        if t.startswith(ql) or n.startswith(ql): return 1
        return 2
    return sorted(rows, key=lambda m: (rank(m), (m['trade_name'] or '').lower()))[:8]

async def main():
    tests = ['glyc', 'glycerin', '56-81-5', 'niacinamide', 'salicylic', 'arbutin', 'zinc']
    for q in tests:
        rows = await search_raw_materials(q, limit=30)
        ranked = rerank(rows, q)
        names = [r['trade_name'] for r in ranked[:4]]
        print(f'{q!r:<15} total={len(rows):>2}  top4={names}')

asyncio.run(main())
