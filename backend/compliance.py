"""
เครื่องมือตรวจสอบการปฏิบัติตามประกาศกระทรวงสาธารณสุข
ว่าด้วยผลิตภัณฑ์เครื่องสำอาง (ASEAN Cosmetic Directive — ACD)
ซึ่งสอดคล้องกับข้อบังคับ EU 1223/2009

ครอบคลุมภาคผนวก:
  II   — สารต้องห้าม (ห้ามใช้เด็ดขาด)
  III  — สารควบคุม (ใช้ได้ภายใต้เงื่อนไขที่กำหนด)
  VI   — สารกันเสียที่อนุญาต
  VII  — ตัวกรองรังสี UV ที่อนุญาต

การจับคู่ใช้ชื่อ INCI ตัวพิมพ์ใหญ่ (O(1) lookup)
หมายเลข CAS บันทึกไว้เป็นข้อมูลอ้างอิง
"""
from typing import Any, Dict, List, Optional

REGULATORY: Dict[str, Dict[str, Any]] = {

    # ── ภาคผนวก II — สารต้องห้าม (แสดงด้วยสีแดง) ─────────────────────
    'BENZENE': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '71-43-2',
        'notes': 'สารก่อมะเร็ง (ระดับ 1A) — ห้ามใช้ในผลิตภัณฑ์เครื่องสำอางโดยเด็ดขาด (ภาคผนวก II)',
    },
    'HEXACHLOROPHENE': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '70-30-4',
        'notes': 'สารต้านจุลชีพที่เป็นพิษต่อระบบประสาท — ห้ามใช้ (ภาคผนวก II)',
    },
    'BITHIONOL': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '97-18-7',
        'notes': 'สารที่ทำให้เกิดความไวแสง — ห้ามใช้ (ภาคผนวก II)',
    },
    'CHLOROFORM': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '67-66-3',
        'notes': 'สาร CMR (ระดับ 2) — ห้ามใช้ (ภาคผนวก II)',
    },
    'TRETINOIN': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '302-79-4',
        'notes': 'เรตินอิก แอซิด — ยาที่ต้องมีใบสั่งแพทย์ ห้ามใช้ในผลิตภัณฑ์เครื่องสำอาง (ภาคผนวก II)',
    },
    'RETINOIC ACID': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '302-79-4',
        'notes': 'ยาที่ต้องมีใบสั่งแพทย์ — ห้ามใช้ในผลิตภัณฑ์เครื่องสำอาง (ภาคผนวก II)',
    },
    'THIMEROSAL': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '54-64-8',
        'notes': 'สารประกอบปรอทอินทรีย์ — ห้ามใช้ (ภาคผนวก II)',
    },
    'PHENYLMERCURIC ACETATE': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '62-38-4',
        'notes': 'สารประกอบปรอทอินทรีย์ — ห้ามใช้ (ภาคผนวก II)',
    },
    'LEAD ACETATE': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '301-04-2',
        'notes': 'สารประกอบตะกั่ว — ห้ามใช้ในผลิตภัณฑ์เครื่องสำอาง (ภาคผนวก II)',
    },
    'MERCURY': {
        'annex': 'II', 'level': 'banned', 'max_pct': None,
        'cas': '7439-97-6',
        'notes': 'ปรอทและสารประกอบอนินทรีย์ — ห้ามใช้ (ภาคผนวก II)',
    },

    # ── ภาคผนวก III — สารควบคุม (แสดงด้วยสีส้ม) ──────────────────────
    'SALICYLIC ACID': {
        'annex': 'III', 'level': 'restricted', 'max_pct': 2.0,
        'cas': '69-72-7',
        'notes': (
            'ใช้ได้ไม่เกิน 2% ในผลิตภัณฑ์ประเภทใช้แล้วทิ้งไว้ (Leave-on) / '
            'ไม่เกิน 3% ในผลิตภัณฑ์ประเภทล้างออก (Rinse-off) '
            'ข้อความคำเตือนบนฉลาก: ห้ามใช้ในเด็กอายุต่ำกว่า 3 ปี '
            '(ภาคผนวก III ลำดับที่ 3)'
        ),
    },
    'RESORCINOL': {
        'annex': 'III', 'level': 'restricted', 'max_pct': 0.5,
        'cas': '108-46-3',
        'notes': 'ใช้ได้ไม่เกิน 0.5% (ผลิตภัณฑ์ย้อมผม) / 0.1% (ผลิตภัณฑ์ประเภทใช้แล้วทิ้งไว้) (ภาคผนวก III ลำดับที่ 54)',
    },
    'HYDROQUINONE': {
        'annex': 'III', 'level': 'restricted', 'max_pct': 2.0,
        'cas': '123-31-9',
        'notes': 'ใช้ได้ไม่เกิน 2% ในภูมิภาคอาเซียน (ภาคผนวก III) หมายเหตุ: ห้ามใช้เพื่อวัตถุประสงค์ทั่วไปในสหภาพยุโรป ต้องระบุข้อความบนฉลาก',
    },
    'KOJIC ACID': {
        'annex': 'III', 'level': 'restricted', 'max_pct': 1.0,
        'cas': '501-30-4',
        'notes': 'ใช้ได้ไม่เกิน 1% ในผลิตภัณฑ์ทาหน้าประเภทใช้แล้วทิ้งไว้ (ตามประกาศ อย. ไทย / ข้อเสนอ EU)',
    },
    'HYDROGEN PEROXIDE': {
        'annex': 'III', 'level': 'restricted', 'max_pct': 4.0,
        'cas': '7722-84-1',
        'notes': 'ใช้ได้ไม่เกิน 4% (ผลิตภัณฑ์ดูแลเส้นผม) / 0.1% (ผลิตภัณฑ์ดูแลช่องปาก) (ภาคผนวก III)',
    },
    'ZINC PYRITHIONE': {
        'annex': 'III', 'level': 'restricted', 'max_pct': 1.0,
        'cas': '13463-41-7',
        'notes': 'ใช้ได้ไม่เกิน 1% เฉพาะในผลิตภัณฑ์ดูแลเส้นผมประเภทล้างออกเท่านั้น (ภาคผนวก III)',
    },

    # ── ภาคผนวก VI — สารกันเสีย (แสดงด้วยสีส้ม) ──────────────────────
    'METHYLPARABEN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.4,
        'cas': '99-76-3',
        'notes': 'ใช้ได้ไม่เกิน 0.4% (ใช้เดี่ยว) / 0.8% (รวมกลุ่มพาราเบน) (ภาคผนวก VI ลำดับที่ 12)',
    },
    'ETHYLPARABEN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.4,
        'cas': '120-47-8',
        'notes': 'ใช้ได้ไม่เกิน 0.4% (ใช้เดี่ยว) / 0.8% (รวมกลุ่มพาราเบน) (ภาคผนวก VI ลำดับที่ 13)',
    },
    'PROPYLPARABEN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.14,
        'cas': '94-13-3',
        'notes': 'ใช้ได้ไม่เกิน 0.14% (ใช้เดี่ยว) / 0.19% (รวมพาราเบนสายยาว) (ภาคผนวก VI ลำดับที่ 14)',
    },
    'BUTYLPARABEN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.14,
        'cas': '94-26-8',
        'notes': 'ใช้ได้ไม่เกิน 0.14% (ใช้เดี่ยว) (ภาคผนวก VI ลำดับที่ 15)',
    },
    'ISOBUTYLPARABEN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.14,
        'cas': '4247-02-3',
        'notes': 'ใช้ได้ไม่เกิน 0.14% (ใช้เดี่ยว) (ภาคผนวก VI)',
    },
    'PHENOXYETHANOL': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 1.0,
        'cas': '122-99-6',
        'notes': 'ใช้ได้ไม่เกิน 1.0% (ภาคผนวก VI ลำดับที่ 29) หลีกเลี่ยงการใช้ในผลิตภัณฑ์สำหรับทารกและเด็กอายุต่ำกว่า 3 ปี',
    },
    'BENZYL ALCOHOL': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 1.0,
        'cas': '100-51-6',
        'notes': 'ใช้ได้ไม่เกิน 1.0% ในฐานะสารกันเสีย (ภาคผนวก VI ลำดับที่ 34) สารก่อภูมิแพ้จากน้ำหอม — ต้องระบุชื่อบนฉลากผลิตภัณฑ์',
    },
    'TRICLOSAN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.3,
        'cas': '3380-34-5',
        'notes': 'ใช้ได้ไม่เกิน 0.3% เฉพาะในผลิตภัณฑ์บางประเภทที่ได้รับอนุญาตเท่านั้น (ภาคผนวก VI ลำดับที่ 46)',
    },
    'CHLORPHENESIN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.3,
        'cas': '104-29-0',
        'notes': 'ใช้ได้ไม่เกิน 0.3% (ภาคผนวก VI ลำดับที่ 48)',
    },
    'DEHYDROACETIC ACID': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.6,
        'cas': '520-45-6',
        'notes': 'ใช้ได้ไม่เกิน 0.6% (รูปแบบกรด) / 0.725% (รูปแบบเกลือโซเดียม) (ภาคผนวก VI ลำดับที่ 9)',
    },
    'DMDM HYDANTOIN': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.6,
        'cas': '6440-58-0',
        'notes': 'ใช้ได้ไม่เกิน 0.6% สารกันเสียประเภทปล่อยฟอร์มาลดีไฮด์ (ภาคผนวก VI ลำดับที่ 23)',
    },
    'IMIDAZOLIDINYL UREA': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.6,
        'cas': '39236-46-9',
        'notes': 'ใช้ได้ไม่เกิน 0.6% สารกันเสียประเภทปล่อยฟอร์มาลดีไฮด์ (ภาคผนวก VI ลำดับที่ 24)',
    },
    'SODIUM BENZOATE': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.5,
        'cas': '532-32-1',
        'notes': 'ใช้ได้ไม่เกิน 0.5% (คำนวณในรูป Benzoic acid) (ภาคผนวก VI ลำดับที่ 1)',
    },
    'POTASSIUM SORBATE': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.6,
        'cas': '24634-61-5',
        'notes': 'ใช้ได้ไม่เกิน 0.6% (คำนวณในรูป Sorbic acid) (ภาคผนวก VI ลำดับที่ 5)',
    },
    'SORBIC ACID': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.6,
        'cas': '110-44-1',
        'notes': 'ใช้ได้ไม่เกิน 0.6% (ภาคผนวก VI ลำดับที่ 5)',
    },
    'BENZOIC ACID': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.5,
        'cas': '65-85-0',
        'notes': 'ใช้ได้ไม่เกิน 0.5% (ภาคผนวก VI ลำดับที่ 1)',
    },
    'CHLORHEXIDINE': {
        'annex': 'VI', 'level': 'restricted', 'max_pct': 0.3,
        'cas': '55-56-1',
        'notes': 'ใช้ได้ไม่เกิน 0.3% (รูปแบบ Digluconate) (ภาคผนวก VI ลำดับที่ 42)',
    },

    # ── ภาคผนวก VII — ตัวกรองรังสี UV (แสดงด้วยสีส้ม) ─────────────────
    'ETHYLHEXYL METHOXYCINNAMATE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 10.0,
        'cas': '5466-77-3',
        'notes': 'ใช้ได้ไม่เกิน 10% สารกันแดด UV-B (Octinoxate) (ภาคผนวก VII ลำดับที่ 13)',
    },
    'BENZOPHENONE-3': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 10.0,
        'cas': '131-57-7',
        'notes': 'ใช้ได้ไม่เกิน 10% สารกันแดด (Oxybenzone) (ภาคผนวก VII ลำดับที่ 4)',
    },
    'BUTYL METHOXYDIBENZOYLMETHANE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 5.0,
        'cas': '70356-09-1',
        'notes': 'ใช้ได้ไม่เกิน 5% สารกันแดด UV-A (Avobenzone) (ภาคผนวก VII ลำดับที่ 5)',
    },
    'OCTOCRYLENE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 10.0,
        'cas': '6197-30-4',
        'notes': 'ใช้ได้ไม่เกิน 10% สารกันแดด (ภาคผนวก VII ลำดับที่ 10)',
    },
    'HOMOSALATE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 10.0,
        'cas': '118-56-9',
        'notes': 'ใช้ได้ไม่เกิน 10% สารกันแดด UV-B (ภาคผนวก VII ลำดับที่ 6)',
    },
    'ETHYLHEXYL SALICYLATE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 5.0,
        'cas': '118-60-5',
        'notes': 'ใช้ได้ไม่เกิน 5% สารกันแดด UV-B (Octisalate) (ภาคผนวก VII ลำดับที่ 7)',
    },
    'TITANIUM DIOXIDE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 25.0,
        'cas': '13463-67-7',
        'notes': 'ใช้ได้ไม่เกิน 25% สารกันแดด (ภาคผนวก VII ลำดับที่ 27) อนุภาคนาโน: ต้องระบุ [nano] บนฉลากผลิตภัณฑ์',
    },
    'ZINC OXIDE': {
        'annex': 'VII', 'level': 'restricted', 'max_pct': 25.0,
        'cas': '1314-13-2',
        'notes': 'ใช้ได้ไม่เกิน 25% สารกันแดด (ภาคผนวก VII ลำดับที่ 30) อนุภาคนาโน: ต้องระบุ [nano] บนฉลากผลิตภัณฑ์',
    },
}


def check_formula(ingredients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    ตรวจสอบส่วนผสมในสูตรเทียบกับฐานข้อมูล ACD

    แต่ละรายการใน ingredients ควรมี:
      inci_name (str), percentage (float),
      material_id (str, optional), trade_name (str, optional)

    คืนค่ารายการที่พบในฐานข้อมูลกฎระเบียบ (ว่าง = ผ่านการตรวจสอบ)
    """
    findings: List[Dict[str, Any]] = []
    for ing in ingredients:
        key = (ing.get('inci_name') or ing.get('name') or '').strip().upper()
        if not key:
            continue
        rule = REGULATORY.get(key)
        if not rule:
            continue
        pct = float(ing.get('percentage') or 0)
        exceeded = rule['level'] == 'banned' or (
            rule['max_pct'] is not None and pct > rule['max_pct']
        )
        findings.append({
            'inci_name':   ing.get('inci_name') or ing.get('name'),
            'trade_name':  ing.get('trade_name'),
            'material_id': ing.get('material_id'),
            'annex':       rule['annex'],
            'level':       rule['level'],
            'max_pct':     rule['max_pct'],
            'actual_pct':  pct,
            'exceeded':    exceeded,
            'cas':         rule.get('cas', ''),
            'notes':       rule['notes'],
        })
    return findings
