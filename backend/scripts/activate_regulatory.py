"""
activate_regulatory.py
=======================
1. Check whether regulatory columns exist in raw_materials.
2. If not, create them via Supabase REST (using rpc or direct PATCH).
3. Patch all regulated substances from the REGULATORY dict +
   the user-specified overrides (Hydroquinone, Mercury, Betamethasone, etc.)
4. Print a final summary.

Run:
    python -m backend.scripts.activate_regulatory
"""
import asyncio, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

import httpx

URL  = os.getenv('SUPABASE_URL', '').rstrip('/')
KEY  = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
REST = f"{URL}/rest/v1"

BASE_H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}
PATCH_H = {**BASE_H, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}

# ── Substances to regulate ────────────────────────────────────────────────────
# Format: (inci_name_pattern, regulatory_status, max_limit_pct | None, warning_text | None)
SUBSTANCE_RULES = [
    # ── Prohibited ─────────────────────────────────────────────────────────
    ('Hydroquinone',             'prohibited', None, 'สารต้องห้าม — ห้ามใช้ในเครื่องสำอางทุกประเภท (ACD Annex II)'),
    ('Mercury',                  'prohibited', None, 'สารต้องห้าม — สารปรอทและสารประกอบปรอท ห้ามใช้'),
    ('Betamethasone',            'prohibited', None, 'สารต้องห้าม — สเตียรอยด์ ห้ามใช้ในเครื่องสำอาง'),
    ('Clobetasol',               'prohibited', None, 'สารต้องห้าม — สเตียรอยด์ ห้ามใช้ในเครื่องสำอาง'),
    ('Lead Acetate',             'prohibited', None, 'สารต้องห้าม — สารตะกั่วและสารประกอบตะกั่ว'),
    ('Chloroform',               'prohibited', None, 'สารต้องห้าม — ACD Annex II'),
    ('Benzene',                  'prohibited', None, 'สารต้องห้าม — ACD Annex II'),
    ('Formaldehyde',             'prohibited', None, 'สารต้องห้าม — ยกเว้นเฉพาะเล็บสูงสุด 5%'),
    ('Retinoic Acid',            'prohibited', None, 'สารต้องห้าม — ห้ามใช้ในเครื่องสำอางทั่วไป (ใช้ได้เฉพาะยา Rx)'),
    ('Triclosan',                'prohibited', None, 'สารต้องห้าม — ห้ามใช้ในเครื่องสำอาง (EU 2019)'),
    # ── Restricted ─────────────────────────────────────────────────────────
    ('Phenoxyethanol',           'restricted', 1.0,
     'ใช้ได้ไม่เกิน 1% — ข้อความคำเตือนบนฉลาก: ไม่แนะนำสำหรับผลิตภัณฑ์เด็กอายุต่ำกว่า 3 ปี (ภาคผนวก V ลำดับที่ 29)'),
    ('Salicylic Acid',           'restricted', 2.0,
     'ใช้ได้ไม่เกิน 2% (leave-on) / 3% (rinse-off) — ข้อความคำเตือนบนฉลาก: ห้ามใช้ในเด็กอายุต่ำกว่า 3 ปี (ภาคผนวก III ลำดับที่ 1)'),
    ('Methylparaben',            'restricted', 0.4,
     'ใช้ได้ไม่เกิน 0.4% (เดี่ยว) หรือ 0.8% (รวมพาราเบนทั้งหมด) (ภาคผนวก VI ลำดับที่ 12)'),
    ('Ethylparaben',             'restricted', 0.4,
     'ใช้ได้ไม่เกิน 0.4% (เดี่ยว) หรือ 0.8% (รวมพาราเบนทั้งหมด)'),
    ('Propylparaben',            'restricted', 0.14,
     'ใช้ได้ไม่เกิน 0.14% (เดี่ยว) หรือ 0.8% (รวมพาราเบนทั้งหมด) (EU 2014)'),
    ('Butylparaben',             'restricted', 0.14,
     'ใช้ได้ไม่เกิน 0.14% (เดี่ยว) หรือ 0.8% (รวมพาราเบนทั้งหมด) (EU 2014)'),
    ('Kojic Acid',               'restricted', 1.0,
     'ใช้ได้ไม่เกิน 1% ในผลิตภัณฑ์ดูแลผิวหน้า — ต้องระบุ: อาจระคายเคืองผิวที่บอบบาง'),
    ('Zinc Oxide',               'restricted', 25.0,
     'ใช้ได้ไม่เกิน 25% เป็นสารกันแดด — อนุภาคนาโนต้องระบุ [nano] บนฉลาก (ภาคผนวก VII ลำดับที่ 30)'),
    ('Titanium Dioxide',         'restricted', 25.0,
     'ใช้ได้ไม่เกิน 25% เป็นสารกันแดด — อนุภาคนาโนต้องระบุ [nano] บนฉลาก'),
    ('Resorcinol',               'restricted', 0.5,
     'ใช้ได้ไม่เกิน 0.5% ในผลิตภัณฑ์ย้อมผม (ภาคผนวก III ลำดับที่ 35)'),
    ('Chlorphenesin',            'restricted', 0.3,
     'ใช้ได้ไม่เกิน 0.3% เป็นสารกันเสีย (ภาคผนวก V ลำดับที่ 42)'),
    ('Benzyl Alcohol',           'restricted', 1.0,
     'ใช้ได้ไม่เกิน 1% เป็นสารกันเสีย (ภาคผนวก V ลำดับที่ 34) ต้องระบุบนฉลาก'),
    ('Sodium Benzoate',          'restricted', 0.5,
     'ใช้ได้ไม่เกิน 0.5% (ค่า pH ≤ 5.5) เป็นสารกันเสีย'),
    ('Dehydroacetic Acid',       'restricted', 0.6,
     'ใช้ได้ไม่เกิน 0.6% เป็นสารกันเสีย (ภาคผนวก V ลำดับที่ 8)'),
    ('DMDM Hydantoin',           'restricted', 0.6,
     'ใช้ได้ไม่เกิน 0.6% — ปล่อย Formaldehyde ต้องระบุ "contains formaldehyde" ถ้า > 0.05%'),
    ('Imidazolidinyl Urea',      'restricted', 0.6,
     'ใช้ได้ไม่เกิน 0.6% — ปล่อย Formaldehyde ต้องระบุบนฉลาก'),
    ('Avobenzone',               'restricted', 5.0,
     'ใช้ได้ไม่เกิน 5% เป็นสารกันแดด (EU/ACD)'),
    ('Ethylhexyl Methoxycinnamate', 'restricted', 10.0,
     'ใช้ได้ไม่เกิน 10% เป็นสารกันแดด (ภาคผนวก VII ลำดับที่ 2)'),
    ('Benzophenone-3',           'restricted', 10.0,
     'ใช้ได้ไม่เกิน 10% เป็นสารกันแดด — ต้องระบุชื่อบนฉลาก: "contains Oxybenzone"'),
    ('Tranexamic Acid',          'restricted', 3.0,
     'ใช้ได้ไม่เกิน 3% ในผลิตภัณฑ์ดูแลผิว (ประกาศ อย. 2562)'),
    ('Ascorbic Acid',            'restricted', 20.0,
     'ใช้ได้ไม่เกิน 20% ในผลิตภัณฑ์ดูแลผิว'),
    ('Niacinamide',              'restricted', 5.0,
     'ใช้ได้ไม่เกิน 5% ตามมาตรฐานความปลอดภัย (แนะนำ SCCS 2021)'),
    ('Alpha-Arbutin',            'restricted', 2.0,
     'ใช้ได้ไม่เกิน 2% ในผลิตภัณฑ์ดูแลผิวหน้า (SCCS/1550/15)'),
    ('Glycolic Acid',            'restricted', 10.0,
     'ใช้ได้ไม่เกิน 10% (consumer) — pH ≥ 3.5 — ต้องระบุคำเตือนการใช้สารกันแดด'),
    ('Lactic Acid',              'restricted', 10.0,
     'ใช้ได้ไม่เกิน 10% (consumer) — pH ≥ 3.5'),
    ('Retinol',                  'restricted', 1.0,
     'ใช้ได้ไม่เกิน 1% ในผลิตภัณฑ์สำหรับผู้ใหญ่ — ไม่แนะนำในผลิตภัณฑ์สำหรับเด็ก (SCCS 2022)'),
]


async def check_columns_exist() -> bool:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            f"{REST}/raw_materials",
            params={'select': 'regulatory_status', 'limit': '1'},
            headers=BASE_H,
        )
    return r.status_code == 200


async def patch_by_inci(inci_pattern: str, payload: dict) -> tuple[int, int]:
    """PATCH all raw_materials where inci_name ilike the pattern.
    Returns (http_status_code, estimated_rows_updated)."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.patch(
            f"{REST}/raw_materials",
            params={'inci_name': f'ilike.{inci_pattern}'},
            json=payload,
            headers=PATCH_H,
        )
    # 204 = success (no content), 200 = success with data
    return r.status_code, (0 if r.status_code not in (200, 201, 204) else 1)


async def main():
    print("=" * 60)
    print("Regulatory Column Activation")
    print("=" * 60)

    # ── Step 1: check columns exist ───────────────────────────────
    print("\n[1] Checking if regulatory columns exist...", end=" ")
    exists = await check_columns_exist()
    if not exists:
        print("NOT FOUND")
        print("""
ERROR: The regulatory columns do not yet exist in Supabase.

Please run the following SQL in Supabase Dashboard > SQL Editor first:

  ALTER TABLE raw_materials
    ADD COLUMN IF NOT EXISTS regulatory_status  VARCHAR(20),
    ADD COLUMN IF NOT EXISTS max_limit_pct      DECIMAL(10,4),
    ADD COLUMN IF NOT EXISTS regulatory_notes   TEXT;

  CREATE INDEX IF NOT EXISTS idx_rm_regulatory_status
    ON raw_materials (regulatory_status)
    WHERE regulatory_status IS NOT NULL;

After running the SQL, re-run this script.
""")
        sys.exit(1)
    print("OK")

    # ── Step 2: patch each substance ─────────────────────────────
    print(f"\n[2] Updating {len(SUBSTANCE_RULES)} regulated substances...")
    ok, err, skipped = 0, 0, 0
    for inci, status, max_pct, notes in SUBSTANCE_RULES:
        payload: dict = {'regulatory_status': status}
        if max_pct is not None:
            payload['max_limit_pct'] = max_pct
        if notes:
            payload['regulatory_notes'] = notes

        code, rows = await patch_by_inci(inci, payload)
        if code in (200, 201, 204):
            ok += 1
            print(f"  OK  {status:<12} {inci}  (max={max_pct}%)")
        else:
            err += 1
            print(f"  ERR HTTP {code}  {inci}")
        await asyncio.sleep(0.05)   # gentle rate-limit

    # ── Step 3: verify a sample ────────────────────────────────────
    print(f"\n[3] Summary: {ok} updated, {err} errors, {skipped} skipped")

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            f"{REST}/raw_materials",
            params={
                'select':    'inci_name,regulatory_status,max_limit_pct',
                'regulatory_status': 'not.is.null',
                'order':     'regulatory_status.asc,inci_name.asc',
                'limit':     '50',
            },
            headers=BASE_H,
        )
    if r.status_code == 200:
        rows_data = r.json()
        print(f"\n[4] Rows with regulatory_status set: {len(rows_data)}")
        for row in rows_data:
            s = row.get('regulatory_status','—')
            m = row.get('max_limit_pct')
            icon = '🔴' if s == 'prohibited' else '🟡' if s == 'restricted' else '🔵'
            print(f"  {icon} {s:<12} {row['inci_name']:<40} max={m}%")
    else:
        print(f"  Could not verify: HTTP {r.status_code}")

    print("\n✓ Done — restart the uvicorn server to pick up changes.")

asyncio.run(main())
