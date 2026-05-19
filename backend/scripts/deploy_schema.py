"""
Schema deployment script — tries multiple strategies in order:
  1. Direct PostgreSQL via DATABASE_URL / SUPABASE_DB_URL
  2. Management API (requires SUPABASE_ACCESS_TOKEN — a Personal Access Token
     from supabase.com/dashboard/account/tokens)

If both fail, prints clear instructions for the Supabase Dashboard SQL Editor.
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print('Missing dependency: python-dotenv  →  pip install python-dotenv')
    sys.exit(1)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = BASE_DIR / 'schema.sql'

DB_URL = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')

if not SCHEMA_FILE.exists():
    print(f'ERROR: schema file not found at {SCHEMA_FILE}')
    sys.exit(1)

schema_sql = SCHEMA_FILE.read_text(encoding='utf-8')

# Extract project ref from SUPABASE_URL (e.g. https://{ref}.supabase.co)
_project_ref = SUPABASE_URL.removeprefix('https://').split('.')[0] if SUPABASE_URL else ''


def deploy_with_postgres() -> bool:
    if not DB_URL:
        return False
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print('psycopg2-binary not installed; skipping direct-DB path.')
        return False

    print('Attempting direct PostgreSQL connection...')
    conn = None
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        print('Schema deployed successfully via direct PostgreSQL.')
        return True
    except Exception as exc:
        print(f'Direct PostgreSQL failed: {exc}')
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def deploy_with_management_api() -> bool:
    """
    Uses the Supabase Management API to run the schema SQL.
    Requires SUPABASE_ACCESS_TOKEN (Personal Access Token) and SUPABASE_URL.
    """
    if not SUPABASE_ACCESS_TOKEN:
        print('SUPABASE_ACCESS_TOKEN not set — skipping Management API path.')
        return False
    if not _project_ref:
        print('Cannot determine project ref from SUPABASE_URL.')
        return False

    try:
        import httpx
    except ImportError:
        print('httpx not installed; skipping Management API path.')
        return False

    url = f'https://api.supabase.com/v1/projects/{_project_ref}/database/query'
    headers = {
        'Authorization': f'Bearer {SUPABASE_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }

    print(f'Deploying schema via Supabase Management API (project: {_project_ref})...')
    try:
        resp = httpx.post(url, json={'query': schema_sql}, headers=headers, timeout=60.0)
        if resp.status_code in (200, 201):
            print('Schema deployed successfully via Management API.')
            return True
        print(f'Management API returned {resp.status_code}: {resp.text[:500]}')
        return False
    except Exception as exc:
        print(f'Management API request failed: {exc}')
        return False


def print_manual_instructions() -> None:
    print('\n' + '=' * 60)
    print('MANUAL DEPLOYMENT — Supabase Dashboard SQL Editor')
    print('=' * 60)
    print(f'  1. Open https://supabase.com/dashboard/project/{_project_ref}/sql/new')
    print(f'  2. Paste the contents of:')
    print(f'       {SCHEMA_FILE}')
    print(f'  3. Click "Run" (Ctrl+Enter)')
    print()
    print('OR — add SUPABASE_ACCESS_TOKEN to .env to enable automated HTTP deploy:')
    print('  Get a Personal Access Token from:')
    print('    https://supabase.com/dashboard/account/tokens')
    print('  Then add to .env:')
    print('    SUPABASE_ACCESS_TOKEN=sbp_...')
    print('=' * 60)


if __name__ == '__main__':
    if deploy_with_postgres():
        sys.exit(0)

    if deploy_with_management_api():
        sys.exit(0)

    print_manual_instructions()
    sys.exit(1)
