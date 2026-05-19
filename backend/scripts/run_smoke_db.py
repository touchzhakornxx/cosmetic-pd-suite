"""
End-to-end smoke test: scrape myskinrecipes -> save to Supabase via HTTP API.
Usage: python backend/scripts/run_smoke_db.py [url]
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv()

import httpx
import os

from backend.db import (
    _supabase_headers, SUPABASE_REST_URL,
    create_scrape_job, update_scrape_job_status, insert_scrape_result,
)
from backend.scrapers.myskinrecipes import MySkinRecipesScraper

DEFAULT_URL = (
    'https://www.myskinrecipes.com/shop/th/'
    'อำพรางริ้วรอย/'
    '2234-quikblur™-polymethylsilsesquioxane-solution-eq-silsoft-e-pearl.html'
)


def _divider(label: str):
    print(f'\n{"-" * 50}')
    print(f'  {label}')
    print('-' * 50)


async def test_db_connectivity():
    """Quick sanity check -can we reach the REST API at all?"""
    _divider('Step 1: REST API connectivity')
    if not SUPABASE_REST_URL:
        print('FAIL: SUPABASE_URL not set')
        return False
    try:
        headers = _supabase_headers()
        # Use a table endpoint — any non-5xx means the API and auth are working
        url = SUPABASE_REST_URL + '/scrape_jobs?limit=1'
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        print(f'  GET /scrape_jobs?limit=1 -> {resp.status_code}')
        if resp.status_code < 500:
            print(f'  OK - API reachable')
            if resp.status_code not in (200, 206):
                print(f'  Note: {resp.text[:200]}')
            return True
        print(f'  FAIL (server error): {resp.text[:300]}')
        return False
    except Exception as exc:
        print(f'  FAIL: {exc}')
        return False


async def test_insert_job(source_url: str) -> str | None:
    """Create a scrape_jobs row and return the remote job ID."""
    _divider('Step 2: Insert scrape_jobs row')
    try:
        headers = _supabase_headers()
        payload = [{'source_url': source_url, 'status': 'running'}]
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                SUPABASE_REST_URL + '/scrape_jobs',
                json=payload,
                headers=headers,
            )
        print(f'  POST /scrape_jobs -> {resp.status_code}')
        if resp.status_code in (200, 201):
            data = resp.json()
            row = data[0] if isinstance(data, list) else data
            job_id = row.get('id')
            print(f'  OK -job_id = {job_id}')
            return job_id
        print(f'  FAIL: {resp.text[:400]}')
        return None
    except Exception as exc:
        print(f'  FAIL: {exc}')
        return None


async def run_scraper(url: str) -> dict:
    _divider('Step 3: Playwright scrape')
    safe_url = url.encode('ascii', errors='replace').decode('ascii')
    print(f'  URL: {safe_url}')
    print('  (this may take up to 30s) ...')
    scraper = MySkinRecipesScraper()
    result = await scraper.scrape(url)
    parsed = result.get('parsed', [])
    errors = result.get('errors', [])
    html_len = len(result.get('raw_html') or '')
    print(f'  raw_html: {html_len} bytes')
    print(f'  parsed items: {len(parsed)}')
    if parsed:
        for item in parsed[:5]:
            pct = f" ({item['percentage']}%)" if item.get('percentage') else ''
            print(f'    * {item["name"]}{pct}')
        if len(parsed) > 5:
            print(f'    ... +{len(parsed) - 5} more')
    if errors:
        print(f'  errors: {errors}')
    return result


async def test_insert_result(job_id: str, result: dict) -> bool:
    _divider('Step 4: Insert scrape_results row')
    parsed = result.get('parsed', [])
    errors = result.get('errors', [])
    raw_html = result.get('raw_html')
    try:
        headers = _supabase_headers()
        payload = [{
            'job_id': job_id,
            'raw_html': raw_html,
            'parsed': parsed,
            'errors': errors or [],
        }]
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                SUPABASE_REST_URL + '/scrape_results',
                json=payload,
                headers=headers,
            )
        print(f'  POST /scrape_results -> {resp.status_code}')
        if resp.status_code in (200, 201):
            data = resp.json()
            row = data[0] if isinstance(data, list) else data
            print(f'  OK -result_id = {row.get("id")}')
            return True
        print(f'  FAIL: {resp.text[:400]}')
        return False
    except Exception as exc:
        print(f'  FAIL: {exc}')
        return False


async def test_update_job(job_id: str, status: str) -> bool:
    _divider('Step 5: Update scrape_jobs status')
    try:
        headers = _supabase_headers()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(
                SUPABASE_REST_URL + f'/scrape_jobs?id=eq.{job_id}',
                json={'status': status},
                headers=headers,
            )
        print(f'  PATCH /scrape_jobs?id=eq.{job_id} -> {resp.status_code}')
        if resp.status_code in (200, 204):
            print(f'  OK -status set to "{status}"')
            return True
        print(f'  FAIL: {resp.text[:300]}')
        return False
    except Exception as exc:
        print(f'  FAIL: {exc}')
        return False


async def main(url: str):
    print('\n=== Supabase DB Smoke Test ===')
    key_label = 'service_role' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'anon'
    print(f'  Auth key: {key_label}')
    print(f'  REST URL: {SUPABASE_REST_URL}')

    ok = await test_db_connectivity()
    if not ok:
        print('\nAborting: cannot reach Supabase REST API.')
        return

    job_id = await test_insert_job(url)
    if not job_id:
        print('\nAborting: failed to create scrape job.')
        print('Likely cause: anon role has no INSERT permission.')
        print('Fix -run in Supabase SQL Editor:')
        print('  GRANT SELECT, INSERT, UPDATE ON scrape_jobs, scrape_results TO anon;')
        print('OR add SUPABASE_SERVICE_ROLE_KEY to .env')
        return

    result = await run_scraper(url)

    saved = await test_insert_result(job_id, result)
    final_status = 'success' if saved else 'failed'
    await test_update_job(job_id, final_status)

    print('\n' + '=' * 50)
    if saved:
        print('  ALL STEPS PASSED -data is live in Supabase')
    else:
        print('  Partial: job created but result save failed')
    print('=' * 50 + '\n')


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    asyncio.run(main(url))
