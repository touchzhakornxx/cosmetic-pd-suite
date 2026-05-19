import httpx, asyncio

async def probe():
    async with httpx.AsyncClient(timeout=25, follow_redirects=True) as c:
        urls = [
            'https://world.openbeautyfacts.org/data/taxonomies/ingredients.json',
            'https://ec.europa.eu/growth/tools-databases/cosing/api/v1/ingredients?page=0&size=50',
            'https://ec.europa.eu/growth/tools-databases/cosing/api/v1/ingredients',
        ]
        for url in urls:
            try:
                r = await c.get(url, headers={'Accept': 'application/json,text/csv,*/*',
                                              'User-Agent': 'Mozilla/5.0'}, timeout=15)
                ct = r.headers.get('content-type', '')
                is_data = ('json' in ct or 'csv' in ct) and b'<html' not in r.content[:10]
                tag = 'DATA' if is_data else 'html'
                print(f'{r.status_code}  {len(r.content):>8}b  {tag}  {url[:70]}')
                if is_data:
                    print('  PREVIEW:', r.text[:300])
            except Exception as e:
                print(f'ERR  {url[:70]}: {e}')

asyncio.run(probe())
