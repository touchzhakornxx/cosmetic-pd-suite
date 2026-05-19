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


# ── ประเภทผลิตภัณฑ์ที่เป็น Rinse-off ─────────────────────────────────────
_RINSE_OFF_TYPES = {
    'Cleanser', 'Shampoo', 'Conditioner', 'Hair Remover',
    'Mouth Wash', 'Tooth Paste', 'Mouth Spray',
    'Nail Remover', 'Cuticle Remover',
}

# ── กฎเฉพาะตามประเภทผลิตภัณฑ์ ─────────────────────────────────────────────
# Key: (inci_name_upper, context) — context คือ product_category หรือ 'rinse-off'/'leave-on'
# Value: override fields (max_pct, notes, level)
PRODUCT_TYPE_OVERRIDES: Dict[tuple, Dict[str, Any]] = {

    # Salicylic Acid — rinse-off ใช้ได้ถึง 3%, leave-on 2%
    ('SALICYLIC ACID', 'rinse-off'): {
        'max_pct': 3.0,
        'notes': 'Rinse-off (Cleanser/Shampoo): ใช้ได้ไม่เกิน 3% — คำเตือน: ห้ามใช้กับเด็กอายุต่ำกว่า 3 ปี (ภาคผนวก III)',
    },
    ('SALICYLIC ACID', 'leave-on'): {
        'max_pct': 2.0,
        'notes': 'Leave-on (Serum/Cream/Toner): ใช้ได้ไม่เกิน 2% — คำเตือน: ห้ามใช้กับเด็กอายุต่ำกว่า 3 ปี (ภาคผนวก III)',
    },

    # Retinol — Skin Care face ใช้ได้ 1%, Body 0.3%
    ('RETINOL', 'Skin Care'): {
        'max_pct': 1.0,
        'notes': 'Skin Care (face): ใช้ได้ไม่เกิน 1% — ห้ามใช้บริเวณรอบดวงตาและในผลิตภัณฑ์เด็ก (SCCS 2022)',
    },
    ('RETINOL', 'Make up'): {
        'max_pct': 0.3,
        'notes': 'Make up: ใช้ได้ไม่เกิน 0.3% — ไม่แนะนำใช้ในผลิตภัณฑ์แต่งหน้าบริเวณดวงตา (SCCS 2022)',
    },

    # Formaldehyde — ห้ามใช้ทั่วไป แต่ใน Nail care ใช้เป็น nail hardener ได้ ≤ 5%
    ('FORMALDEHYDE', 'Nail care'): {
        'level': 'restricted',
        'max_pct': 5.0,
        'notes': 'Nail hardener: ใช้ได้ไม่เกิน 5% — ห้ามสัมผัสผิวหนัง ต้องมีคำแนะนำป้องกันบนฉลาก (ภาคผนวก III)',
    },

    # Resorcinol — ใช้ใน Hair dye เท่านั้น
    ('RESORCINOL', 'Hair care'): {
        'max_pct': 0.5,
        'notes': 'Hair dye/ย้อมผม: ใช้ได้ไม่เกิน 0.5% — ต้องระบุบนฉลาก: "มีเรซอร์ซินอล — ล้างออกหลังใช้งาน" (ภาคผนวก III)',
    },

    # Kojic Acid — จำกัดเฉพาะ Skin Care
    ('KOJIC ACID', 'Skin Care'): {
        'max_pct': 1.0,
        'notes': 'Skin Care: ใช้ได้ไม่เกิน 1% ในผลิตภัณฑ์ผิวหน้า — ต้องระบุคำเตือนการใช้งานบนฉลาก (ประกาศ อย.)',
    },

    # Alpha-Arbutin — จำกัดเฉพาะ Skin Care
    ('ALPHA-ARBUTIN', 'Skin Care'): {
        'max_pct': 2.0,
        'notes': 'Skin Care (face): ใช้ได้ไม่เกิน 2% — สำหรับผลิตภัณฑ์ทาตัวแนะนำไม่เกิน 0.5% (SCCS/1550/15)',
    },

    # Zinc Oxide / Titanium Dioxide — ใช้ใน Make up เป็นสารให้สี opacifier
    ('ZINC OXIDE', 'Make up'): {
        'max_pct': 25.0,
        'notes': 'Make up: ใช้เป็น opacifier/colorant ได้ไม่เกิน 25% — อนุภาคนาโนต้องระบุ [nano] บนฉลาก',
    },
    ('TITANIUM DIOXIDE', 'Make up'): {
        'max_pct': 25.0,
        'notes': 'Make up: ใช้เป็น opacifier/colorant ได้ไม่เกิน 25% — อนุภาคนาโนต้องระบุ [nano] บนฉลาก',
    },

    # Glycolic Acid / Lactic Acid — leave-on เข้มกว่า rinse-off
    ('GLYCOLIC ACID', 'rinse-off'): {
        'max_pct': 10.0,
        'notes': 'Rinse-off: ใช้ได้ไม่เกิน 10% — ต้องระบุคำเตือนการใช้สารกันแดดร่วม',
    },
    ('LACTIC ACID', 'rinse-off'): {
        'max_pct': 10.0,
        'notes': 'Rinse-off: ใช้ได้ไม่เกิน 10% — pH ≥ 3.5',
    },

    # Niacinamide — ใช้ใน Skin Care แนะนำไม่เกิน 5%
    ('NIACINAMIDE', 'Skin Care'): {
        'max_pct': 5.0,
        'notes': 'Skin Care: แนะนำไม่เกิน 5% — ความเข้มข้นสูงอาจทำให้ผิวแดงและระคายเคือง (SCCS 2021)',
    },
}


def check_formula(
    ingredients: List[Dict[str, Any]],
    product_category: Optional[str] = None,
    product_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    ตรวจสอบส่วนผสมในสูตรเทียบกับฐานข้อมูล ACD
    รองรับกฎเฉพาะตาม product_category และ product_type
    """
    is_rinse = (product_type or '') in _RINSE_OFF_TYPES
    app_context = 'rinse-off' if is_rinse else 'leave-on'

    findings: List[Dict[str, Any]] = []
    for ing in ingredients:
        key = (ing.get('inci_name') or ing.get('name') or '').strip().upper()
        if not key:
            continue
        rule = REGULATORY.get(key)
        if not rule:
            continue

        # ค้นหา override ตามลำดับความสำคัญ:
        # 1. product_category เฉพาะ (เช่น 'Nail care', 'Hair care')
        # 2. rinse-off / leave-on
        override = {}
        if product_category:
            override = PRODUCT_TYPE_OVERRIDES.get((key, product_category), {})
        if not override:
            override = PRODUCT_TYPE_OVERRIDES.get((key, app_context), {})

        effective_level   = override.get('level',   rule['level'])
        effective_max_pct = override.get('max_pct', rule['max_pct'])
        effective_notes   = override.get('notes',   rule['notes'])
        rule_source       = 'product-type' if override else 'general'

        pct = float(ing.get('percentage') or 0)
        exceeded = effective_level == 'banned' or (
            effective_max_pct is not None and pct > effective_max_pct
        )
        findings.append({
            'inci_name':   ing.get('inci_name') or ing.get('name'),
            'trade_name':  ing.get('trade_name'),
            'material_id': ing.get('material_id'),
            'annex':       rule['annex'],
            'level':       effective_level,
            'max_pct':     effective_max_pct,
            'actual_pct':  pct,
            'exceeded':    exceeded,
            'cas':         rule.get('cas', ''),
            'notes':       effective_notes,
            'rule_source': rule_source,
        })
    return findings
