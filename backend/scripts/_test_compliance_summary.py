import asyncio, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv; load_dotenv(ROOT / '.env')
from backend.compliance import REGULATORY, check_formula
from backend.db import fetch_all_formula_ingredients
from collections import defaultdict

async def main():
    # DB stats
    banned           = sum(1 for v in REGULATORY.values() if v.get('level') == 'banned')
    restricted       = sum(1 for v in REGULATORY.values() if v.get('level') == 'restricted')
    warning_required = sum(1 for v in REGULATORY.values()
                           if 'คำเตือน' in v.get('notes', '') or 'ฉลาก' in v.get('notes', ''))
    print(f"Regulatory DB: total={len(REGULATORY)}  banned={banned}  restricted={restricted}  warning={warning_required}")

    # Formula violations
    rows = await fetch_all_formula_ingredients()
    print(f"Formula ingredient rows fetched: {len(rows)}")

    by_formula = defaultdict(list)
    for row in rows:
        rm = row.get('raw_materials') or {}
        by_formula[row['formula_id']].append({
            'inci_name':  rm.get('inci_name', ''),
            'trade_name': rm.get('trade_name', ''),
            'percentage': row.get('percentage', 0),
        })
    print(f"Formulas found: {len(by_formula)}")

    violations = []
    for fid, ings in by_formula.items():
        findings = check_formula(ings)
        if findings:
            violations.append((fid, len(findings)))
            for f in findings:
                print(f"  [{fid[:8]}] {f['inci_name']} {f['percentage']}% -> {f['level']} exceeded={f.get('exceeded')}")

    print(f"\nFormulas with violations: {len(violations)}")

asyncio.run(main())
