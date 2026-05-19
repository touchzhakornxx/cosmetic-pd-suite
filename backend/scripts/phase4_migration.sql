-- Phase 4: FDA / ASEAN Compliance & CAS Mapping
-- Run this in the Supabase Dashboard → SQL Editor
-- (Project → SQL Editor → New query → paste → Run)

-- 1. Add CAS number to raw_materials inventory
ALTER TABLE raw_materials
  ADD COLUMN IF NOT EXISTS cas_number VARCHAR(50);

-- 2. Regulatory substances reference table
CREATE TABLE IF NOT EXISTS regulatory_substances (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inci_name       VARCHAR(255) NOT NULL,
    cas_number      VARCHAR(50),
    annex_type      VARCHAR(10)  NOT NULL,          -- 'II' | 'III' | 'VI' | 'VII'
    level           VARCHAR(20)  NOT NULL DEFAULT 'restricted', -- 'banned' | 'restricted'
    max_concentration DECIMAL(7, 4),               -- NULL = banned (no limit concept)
    product_scope   TEXT,                           -- 'leave-on' | 'rinse-off' | 'all'
    notes           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reg_inci ON regulatory_substances (LOWER(inci_name));
CREATE INDEX IF NOT EXISTS idx_reg_cas  ON regulatory_substances (cas_number);
