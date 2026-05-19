import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.scrapers.myskinrecipes import MySkinRecipesScraper


async def main(url: str, out_path: str):
    scraper = MySkinRecipesScraper()
    res = await scraper.scrape(url)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f'Wrote {p}')


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('out')
    args = p.parse_args()
    asyncio.run(main(args.url, args.out))
