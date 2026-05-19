-- เปิดใช้งาน Extension สำหรับเจน ID อัตโนมัติ
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- สร้างตัวแปรประเภทข้อมูลเฉพาะ (Enums)
CREATE TYPE target_skin_enum AS ENUM ('face', 'body', 'rinse-off');
CREATE TYPE formula_status_enum AS ENUM ('draft', 'stability_testing', 'approved', 'rejected');
CREATE TYPE stability_condition_enum AS ENUM ('RT', '40C', '45C', 'Freeze-Thaw');
CREATE TYPE stability_period_enum AS ENUM ('Week1', 'Month1', 'Month3');
CREATE TYPE stability_status_enum AS ENUM ('pass', 'fail', 'pending');
-- 1. ตารางคลังวัตถุดิบ (Raw Materials)
CREATE TABLE raw_materials (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
trade_name VARCHAR(255) NOT NULL,
inci_name VARCHAR(255) NOT NULL,
supplier VARCHAR(255),
function_category VARCHAR(100),
price_per_kg DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
documents_url TEXT,
is_active BOOLEAN DEFAULT TRUE,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- 2. ตารางโปรเจกต์สูตร (Formulas)
CREATE TABLE formulas (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
formula_code VARCHAR(50) UNIQUE NOT NULL,
product_name VARCHAR(255) NOT NULL,
target_skin_type target_skin_enum NOT NULL,
batch_size_g DECIMAL(10, 2) NOT NULL DEFAULT 100.00,
loss_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0.00, -- อัตราสูญเสียระหว่างผลิต (%)
status formula_status_enum DEFAULT 'draft',
mockup_image_url TEXT,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- 3. ตารางส่วนประกอบในสูตร (Formula Ingredients - Many to Many)
CREATE TABLE formula_ingredients (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
formula_id UUID REFERENCES formulas(id) ON DELETE CASCADE,
material_id UUID REFERENCES raw_materials(id),
phase VARCHAR(10) NOT NULL, -- เฟสสาร เช่น A, B, C, D
percentage DECIMAL(7, 4) NOT NULL, -- สัดส่วนเปอร์เซ็นต์ (เช่น 5.0000)
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT check_percentage_positive CHECK (percentage > 0)
);
-- 4. ตารางบันทึกผลความคงตัว (Stability Tests)
CREATE TABLE stability_tests (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
formula_id UUID REFERENCES formulas(id) ON DELETE CASCADE,
condition stability_condition_enum NOT NULL,
check_period stability_period_enum NOT NULL,
ph_value DECIMAL(4, 2),
viscosity VARCHAR(100),
status stability_status_enum DEFAULT 'pending',
notes TEXT,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Scraper job and result storage
CREATE TABLE scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scrape_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES scrape_jobs(id) ON DELETE CASCADE,
    raw_html TEXT,
    parsed JSONB,
    errors TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);