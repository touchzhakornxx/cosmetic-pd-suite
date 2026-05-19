import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.scrapers.myskinrecipes import MySkinRecipesScraper


async def main(url: str):
    scraper = MySkinRecipesScraper()
    res = await scraper.scrape(url)
    parsed = res.get('parsed')
    print(json.dumps({'parsed': parsed}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('url')
    args = p.parse_args()
    asyncio.run(main(args.url))
