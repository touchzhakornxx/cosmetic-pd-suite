-- ============================================================
-- P&D Intelligence Suite — Raw Materials Seed Script
-- 84 ingredients across 11 functional categories
--
-- HOW TO RUN:
--   Supabase Dashboard → SQL Editor → paste → Run
--
-- PREREQUISITES:
--   The cas_number column must exist.  If you skipped the Phase 4
--   migration, run this first:
--     ALTER TABLE raw_materials ADD COLUMN IF NOT EXISTS cas_number VARCHAR(50);
--
-- COLUMNS USED:
--   trade_name      — commercial / lab name
--   inci_name       — INCI standard name (used for compliance lookups)
--   cas_number      — CAS Registry Number
--   supplier        — repurposed here as Function Category
--   is_active       — TRUE for all seed entries
--   price_per_kg    — indicative USD/kg market price (update to local cost)
--
-- USAGE % RANGES are in the inline comments on each row.
-- ============================================================

INSERT INTO raw_materials (trade_name, inci_name, cas_number, supplier, is_active, price_per_kg)
VALUES

-- ── WHITENING & BRIGHTENING ACTIVES ──────────────────────────────────────
('Niacinamide BP',                'Niacinamide',                             '98-92-0',       'Whitening Active', TRUE,  15.00),  -- 2–5 %
('Alpha-Arbutin',                 'Alpha-Arbutin',                           '84380-01-8',    'Whitening Active', TRUE, 180.00),  -- 0.5–2 %
('Beta-Arbutin',                  'Arbutin',                                 '497-76-7',      'Whitening Active', TRUE,  30.00),  -- 1–3 %
('Kojic Acid',                    'Kojic Acid',                              '501-30-4',      'Whitening Active', TRUE,  35.00),  -- 0.5–2 %
('Ascorbic Acid (L-C)',           'Ascorbic Acid',                           '50-81-7',       'Whitening Active', TRUE,   8.00),  -- 5–20 %
('Sodium Ascorbyl Phosphate',     'Sodium Ascorbyl Phosphate',               '66170-10-3',    'Whitening Active', TRUE,  45.00),  -- 2–5 %
('Magnesium Ascorbyl Phosphate',  'Magnesium Ascorbyl Phosphate',            '113170-55-1',   'Whitening Active', TRUE,  55.00),  -- 2–5 %
('Ascorbyl Glucoside',            'Ascorbyl Glucoside',                      '129499-78-1',   'Whitening Active', TRUE,  90.00),  -- 2–5 %
('Tranexamic Acid',               'Tranexamic Acid',                         '1197-18-8',     'Whitening Active', TRUE,  60.00),  -- 2–5 %
('Azelaic Acid',                  'Azelaic Acid',                            '123-99-9',      'Whitening Active', TRUE,  25.00),  -- 5–20 %
('4-Butylresorcinol',             '4-Butylresorcinol',                       '18979-61-8',    'Whitening Active', TRUE, 350.00),  -- 0.1–0.3 %
('Phytic Acid',                   'Phytic Acid',                             '83-86-3',       'Whitening Active', TRUE,  20.00),  -- 0.5–3 %

-- ── ANTI-AGING ACTIVES ───────────────────────────────────────────────────
('Retinol (Oil, 1M IU/g)',        'Retinol',                                 '68-26-8',       'Anti-aging Active', TRUE, 500.00), -- 0.025–1 %
('Retinyl Palmitate',             'Retinyl Palmitate',                       '79-81-2',       'Anti-aging Active', TRUE,  80.00), -- 0.1–2 %
('Bakuchiol',                     'Bakuchiol',                               '10309-37-2',    'Anti-aging Active', TRUE, 250.00), -- 0.5–2 %
('Adenosine',                     'Adenosine',                               '58-61-7',       'Anti-aging Active', TRUE,  80.00), -- 0.04 %
('Argireline Solution 10%',       'Acetyl Hexapeptide-3',                    '616204-22-9',   'Anti-aging Active', TRUE, 120.00), -- 5–10 % of solution
('Resveratrol',                   'Resveratrol',                             '501-36-0',      'Anti-aging Active', TRUE, 200.00), -- 0.1–1 %
('Ceramide NP',                   'Ceramide NP',                             '100403-19-8',   'Anti-aging Active', TRUE, 300.00), -- 0.5–5 %
('Ceramide AP',                   'Ceramide AP',                             '18396-21-1',    'Anti-aging Active', TRUE, 320.00), -- 0.5–5 %
('Palmitoyl Tripeptide-1',        'Palmitoyl Tripeptide-1',                  '147732-56-7',   'Anti-aging Active', TRUE, 450.00), -- 0.1–4 % (sol.)
('Epigallocatechin Gallate',      'Epigallocatechin Gallate',                '989-51-5',      'Anti-aging Active', TRUE, 150.00), -- 0.1–1 %

-- ── HUMECTANTS & MOISTURIZERS ────────────────────────────────────────────
('Glycerin (Kosher)',              'Glycerin',                                '56-81-5',       'Humectant',         TRUE,   2.00), -- 2–20 %
('Sodium Hyaluronate (LMW)',      'Sodium Hyaluronate',                      '9067-32-7',     'Humectant',         TRUE, 250.00), -- 0.01–2 %
('Panthenol DL-',                 'Panthenol',                               '81-13-0',       'Humectant',         TRUE,  20.00), -- 1–5 %
('Sodium PCA',                    'Sodium PCA',                              '28874-51-3',    'Humectant',         TRUE,  18.00), -- 1–5 %
('Betaine Anhydrous',             'Betaine',                                 '107-43-7',      'Humectant',         TRUE,   5.00), -- 1–5 %
('Trehalose',                     'Trehalose',                               '99-20-7',       'Humectant',         TRUE,  15.00), -- 1–5 %
('Allantoin',                     'Allantoin',                               '97-59-6',       'Humectant',         TRUE,  12.00), -- 0.1–2 %
('Urea (Cosmetic Grade)',         'Urea',                                    '57-13-6',       'Humectant',         TRUE,   3.00), -- 5–40 %
('Sorbitol 70%',                  'Sorbitol',                                '50-70-4',       'Humectant',         TRUE,   1.50), -- 2–10 %
('Propylene Glycol',              'Propylene Glycol',                        '57-55-6',       'Humectant',         TRUE,   2.50), -- 1–10 %

-- ── EMOLLIENTS, OILS & SILICONES ─────────────────────────────────────────
('Squalane (Plant-derived)',       'Squalane',                                '111-01-3',      'Emollient',         TRUE,  18.00), -- 2–10 %
('Caprylic/Capric Triglyceride',  'Caprylic/Capric Triglyceride',            '65381-09-1',    'Emollient',         TRUE,   4.00), -- 5–30 %
('Dimethicone 350 cSt',           'Dimethicone',                             '9006-65-9',     'Emollient / Silicone', TRUE, 6.00), -- 1–10 %
('Cyclopentasiloxane',            'Cyclopentasiloxane',                      '541-02-6',      'Emollient / Silicone', TRUE, 8.00), -- 5–25 %
('C12-15 Alkyl Benzoate',         'C12-15 Alkyl Benzoate',                   '68411-27-8',    'Emollient',         TRUE,   5.00), -- 2–10 %
('Isopropyl Myristate',           'Isopropyl Myristate',                     '110-27-0',      'Emollient',         TRUE,   3.50), -- 5–15 %
('Isononyl Isononanoate',         'Isononyl Isononanoate',                   '42131-25-9',    'Emollient',         TRUE,   4.50), -- 2–10 %
('Jojoba Oil',                    'Simmondsia Chinensis Seed Oil',            '61789-91-1',    'Emollient / Oil',   TRUE,  30.00), -- 2–20 %
('Argan Oil',                     'Argania Spinosa Kernel Oil',               '223748-82-1',   'Emollient / Oil',   TRUE,  80.00), -- 2–20 %
('Rosehip Oil',                   'Rosa Canina Fruit Oil',                    '84603-93-0',    'Emollient / Oil',   TRUE,  60.00), -- 2–10 %

-- ── SURFACTANTS ──────────────────────────────────────────────────────────
('Sodium Lauryl Sulfate',         'Sodium Lauryl Sulfate',                   '151-21-3',      'Surfactant (Anionic)',    TRUE,  3.00), -- 1–15 %
('SLES 70%',                      'Sodium Laureth Sulfate',                  '9004-82-4',     'Surfactant (Anionic)',    TRUE,  2.00), -- 5–20 %
('Cocamidopropyl Betaine 30%',    'Cocamidopropyl Betaine',                  '61789-40-0',    'Surfactant (Amphoteric)', TRUE,  3.50), -- 3–10 %
('Sodium Cocoyl Isethionate',     'Sodium Cocoyl Isethionate',               '61789-32-0',    'Surfactant (Anionic)',    TRUE,  8.00), -- 5–30 %
('Decyl Glucoside',               'Decyl Glucoside',                         '68515-73-1',    'Surfactant (Nonionic)',   TRUE,  7.00), -- 5–15 %
('Coco Glucoside',                'Coco Glucoside',                          '68515-73-1',    'Surfactant (Nonionic)',   TRUE,  8.00), -- 5–15 %
('Lauryl Glucoside',              'Lauryl Glucoside',                        '110615-47-9',   'Surfactant (Nonionic)',   TRUE,  7.50), -- 5–15 %
('Sodium Cocoyl Glutamate',       'Sodium Cocoyl Glutamate',                 '68187-30-4',    'Surfactant (Anionic)',    TRUE, 12.00), -- 3–15 %

-- ── EMULSIFIERS ──────────────────────────────────────────────────────────
('Glyceryl Stearate SE',          'Glyceryl Stearate',                       '31566-31-1',    'Emulsifier',        TRUE,   5.00), -- 1–5 %
('Cetearyl Alcohol',              'Cetearyl Alcohol',                        '67762-27-0',    'Emulsifier / Fatty Alcohol', TRUE, 3.50), -- 2–6 %
('Cetyl Alcohol',                 'Cetyl Alcohol',                           '36653-82-4',    'Emulsifier / Fatty Alcohol', TRUE, 3.00), -- 1–5 %
('Polysorbate 20',                'Polysorbate 20',                          '9005-64-5',     'Emulsifier',        TRUE,   4.00), -- 0.5–5 %
('Polysorbate 80',                'Polysorbate 80',                          '9005-65-6',     'Emulsifier',        TRUE,   4.50), -- 0.5–5 %
('Sorbitan Stearate',             'Sorbitan Stearate',                       '1338-41-6',     'Emulsifier',        TRUE,   5.50), -- 1–5 %
('Stearic Acid (Triple Pressed)', 'Stearic Acid',                            '57-11-4',       'Emulsifier / Thickener', TRUE, 2.50), -- 1–5 %
('Lecithin (Sunflower)',          'Lecithin',                                '8002-43-5',     'Emulsifier',        TRUE,  12.00), -- 0.5–3 %

-- ── THICKENERS & GELLING AGENTS ──────────────────────────────────────────
('Carbomer 980',                  'Carbomer',                                '9003-01-4',     'Thickener / Gelling', TRUE, 12.00), -- 0.1–1 %
('Acrylates/C10-30 Crosspolymer', 'Acrylates/C10-30 Alkyl Acrylate Crosspolymer', '9062-04-8', 'Thickener / Gelling', TRUE, 14.00), -- 0.1–1 %
('Xanthan Gum',                   'Xanthan Gum',                             '11138-66-2',    'Thickener / Gelling', TRUE,  8.00), -- 0.1–0.5 %
('Hydroxyethylcellulose',         'Hydroxyethylcellulose',                   '9004-62-0',     'Thickener / Gelling', TRUE, 10.00), -- 0.1–2 %
('HPMC (Methocel)',               'Hydroxypropyl Methylcellulose',           '9004-65-3',     'Thickener / Gelling', TRUE, 11.00), -- 0.1–2 %
('Sodium Polyacrylate',           'Sodium Polyacrylate',                     '9003-04-7',     'Thickener / Gelling', TRUE,  9.00), -- 0.1–2 %

-- ── PRESERVATIVES ────────────────────────────────────────────────────────
('Phenoxyethanol',                'Phenoxyethanol',                          '122-99-6',      'Preservative',      TRUE,   8.00), -- 0.5–1 %
('Ethylhexylglycerin',            'Ethylhexylglycerin',                      '70445-33-9',    'Preservative',      TRUE,  25.00), -- 0.1–1 %
('Benzyl Alcohol',                'Benzyl Alcohol',                          '100-51-6',      'Preservative',      TRUE,   5.00), -- 0.1–1 %
('Sodium Benzoate',               'Sodium Benzoate',                         '532-32-1',      'Preservative',      TRUE,   2.50), -- 0.05–0.5 %
('Potassium Sorbate',             'Potassium Sorbate',                       '24634-61-5',    'Preservative',      TRUE,   3.00), -- 0.05–0.3 %
('Caprylyl Glycol',               'Caprylyl Glycol',                         '1117-86-8',     'Preservative',      TRUE,  18.00), -- 0.1–1 %
('1,2-Hexanediol',                '1,2-Hexanediol',                          '6920-22-5',     'Preservative',      TRUE,  15.00), -- 0.5–2 %
('Chlorphenesin',                 'Chlorphenesin',                           '104-29-0',      'Preservative',      TRUE,  20.00), -- 0.1–0.3 %

-- ── pH ADJUSTERS ─────────────────────────────────────────────────────────
('Citric Acid (Anhydrous)',       'Citric Acid',                             '77-92-9',       'pH Adjuster',       TRUE,   2.00), -- q.s. to target pH
('Sodium Hydroxide 50% Sol.',     'Sodium Hydroxide',                        '1310-73-2',     'pH Adjuster',       TRUE,   0.80), -- q.s. to target pH
('Triethanolamine 99%',           'Triethanolamine',                         '102-71-6',      'pH Adjuster',       TRUE,   3.00), -- q.s. to target pH
('Lactic Acid 88%',               'Lactic Acid',                             '50-21-5',       'pH Adjuster / AHA', TRUE,   3.50), -- q.s. or 2–10 % AHA

-- ── EXFOLIANTS (AHAs / BHAs) ─────────────────────────────────────────────
('Glycolic Acid 70%',             'Glycolic Acid',                           '79-14-1',       'Exfoliant (AHA)',   TRUE,  12.00), -- 1–10 %
('Salicylic Acid',                'Salicylic Acid',                          '69-72-7',       'Exfoliant (BHA)',   TRUE,  10.00), -- 0.5–2 %
('Mandelic Acid',                 'Mandelic Acid',                           '90-64-2',       'Exfoliant (AHA)',   TRUE,  18.00), -- 1–10 %
('Malic Acid',                    'Malic Acid',                              '6915-15-7',     'Exfoliant (AHA)',   TRUE,   6.00), -- 1–5 %

-- ── UV FILTERS ───────────────────────────────────────────────────────────
('Zinc Oxide (Nano-free)',        'Zinc Oxide',                              '1314-13-2',     'UV Filter (Inorganic)', TRUE, 10.00), -- 5–25 %
('Titanium Dioxide (Coated)',     'Titanium Dioxide',                        '13463-67-7',    'UV Filter (Inorganic)', TRUE,  8.00), -- 1–25 %
('Octinoxate (OMC)',              'Ethylhexyl Methoxycinnamate',             '5466-77-3',     'UV Filter (Organic)',   TRUE, 12.00), -- 2–10 %
('Tinosorb S (BEMT)',             'Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine', '187393-00-6', 'UV Filter (Organic)', TRUE, 80.00) -- 1–5 %

;

-- ============================================================
-- VERIFY:  SELECT count(*) FROM raw_materials;
-- RESET:   DELETE FROM raw_materials WHERE supplier LIKE '% Active'
--          OR supplier LIKE 'Humectant'  -- etc. (run per-category)
-- ============================================================
