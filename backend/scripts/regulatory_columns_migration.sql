-- ================================================================
-- Regulatory columns migration for raw_materials
-- Run in: Supabase Dashboard → SQL Editor
--
-- Adds three columns to raw_materials so regulatory status can be
-- stored per ingredient, enabling filtering/search by compliance tier.
-- ================================================================

ALTER TABLE raw_materials
  ADD COLUMN IF NOT EXISTS regulatory_status  VARCHAR(20),   -- 'prohibited' | 'restricted' | 'warning' | NULL
  ADD COLUMN IF NOT EXISTS max_limit_pct      DECIMAL(10,4), -- max allowed % (e.g. 1.00 for Phenoxyethanol)
  ADD COLUMN IF NOT EXISTS regulatory_notes   TEXT;          -- full Thai label/warning text

-- Optional index for fast dashboard queries
CREATE INDEX IF NOT EXISTS idx_rm_regulatory_status
  ON raw_materials (regulatory_status)
  WHERE regulatory_status IS NOT NULL;

-- ── Seed from ASEAN/EU CosDir data ──────────────────────────────
-- Run the companion Python script to populate these from the
-- built-in REGULATORY dict:
--
--   python -m backend.scripts.populate_regulatory_columns
--
-- Or paste updates manually, e.g.:
UPDATE raw_materials SET regulatory_status = 'restricted', max_limit_pct = 1.00,
  regulatory_notes = 'ใช้ได้ไม่เกิน 1% — ฉลากต้องระบุคำเตือน'
WHERE UPPER(inci_name) = 'PHENOXYETHANOL';

UPDATE raw_materials SET regulatory_status = 'restricted', max_limit_pct = 2.00,
  regulatory_notes = 'ใช้ได้ไม่เกิน 2% (leave-on) / 3% (rinse-off) — ห้ามใช้ในเด็ก < 3 ปี'
WHERE UPPER(inci_name) = 'SALICYLIC ACID';

UPDATE raw_materials SET regulatory_status = 'restricted', max_limit_pct = 5.00,
  regulatory_notes = 'ใช้ได้ไม่เกิน 5% ในสูตรล้างออก'
WHERE UPPER(inci_name) = 'KOJIC ACID';

UPDATE raw_materials SET regulatory_status = 'restricted', max_limit_pct = 25.00,
  regulatory_notes = 'ใช้ได้ไม่เกิน 25% เป็นสารกันแดด — อนุภาคนาโนต้องระบุ [nano] บนฉลาก'
WHERE UPPER(inci_name) = 'ZINC OXIDE';

UPDATE raw_materials SET regulatory_status = 'restricted', max_limit_pct = 25.00,
  regulatory_notes = 'ใช้ได้ไม่เกิน 25% เป็นสารกันแดด'
WHERE UPPER(inci_name) = 'TITANIUM DIOXIDE';

UPDATE raw_materials SET regulatory_status = 'prohibited'
WHERE UPPER(inci_name) IN (
  'MERCURY', 'LEAD ACETATE', 'CHLOROFORM', 'BENZENE',
  'FORMALDEHYDE', '1,4-DIOXANE', 'DIETHYLENE GLYCOL'
);

-- ================================================================
-- VERIFY:
--   SELECT inci_name, regulatory_status, max_limit_pct
--   FROM raw_materials
--   WHERE regulatory_status IS NOT NULL
--   ORDER BY regulatory_status, inci_name;
-- ================================================================
