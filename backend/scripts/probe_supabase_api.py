import os
import httpx
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL:
    raise SystemExit('SUPABASE_URL is not set')

print('Supabase URL:', SUPABASE_URL)
print('SUPABASE_ANON_KEY:', 'set' if SUPABASE_ANON_KEY else 'missing')
print('SUPABASE_SERVICE_ROLE_KEY:', 'set' if SUPABASE_SERVICE_ROLE_KEY else 'missing')
print('---')

for path in ['/rest/v1', '/rest/v1/rpc', '/rest/v1/rpc/']:
    url = f"{SUPABASE_URL}{path}"
    try:
        resp = httpx.get(url, timeout=10.0)
        print(url)
        print(resp.status_code)
        print(resp.text[:800])
        print('---')
    except Exception as exc:
        print(url)
        print('ERROR', exc)
        print('---')

if SUPABASE_SERVICE_ROLE_KEY:
    print('Probing authenticated Supabase REST endpoint with service role key...')
    auth_headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    }
    auth_url = f"{SUPABASE_URL}/rest/v1"
    try:
        auth_resp = httpx.get(auth_url, headers=auth_headers, timeout=10.0)
        print(auth_url)
        print(auth_resp.status_code)
        print(auth_resp.text[:800])
    except Exception as exc:
        print(auth_url)
        print('ERROR', exc)
