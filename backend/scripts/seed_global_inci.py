"""
seed_global_inci.py
====================
Populate raw_materials from open-source INCI databases.

Sources tried in order:
  1. Open Beauty Facts ingredient taxonomy  (~10 000+ INCI entries, JSON, direct download)
  2. Embedded curated list                  (~600 industry-standard ingredients)

Usage:
    cd c:\\Users\\TACHAGONXX\\Desktop\\PD
    python -m backend.scripts.seed_global_inci
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
BATCH_SIZE   = 150    # conservative batch size
BATCH_DELAY  = 0.5   # seconds between batches

OBF_URL = 'https://world.openbeautyfacts.org/data/taxonomies/ingredients.json'

# ── helpers ──────────────────────────────────────────────────────────────────

def _row(trade: str, inci: str, cas: str = '', cat: str = '', price: float = 0.0) -> Dict:
    # Only include fields we have actual values for; omitting a key lets the
    # Supabase column default apply (price_per_kg has NOT NULL + DEFAULT 0.00).
    row: Dict = {
        'trade_name': trade.strip()[:200],
        'inci_name':  inci.strip()[:200],
        'is_active':  True,
    }
    if cas:
        row['cas_number'] = cas.strip()[:50]
    if cat:
        row['supplier'] = cat.strip()[:100]
    if price:
        row['price_per_kg'] = float(price)
    return row

def _slug_to_name(slug: str) -> str:
    """'en:sodium-hyaluronate' -> 'Sodium Hyaluronate'"""
    name = re.sub(r'^[a-z]{2}:', '', slug)
    return name.replace('-', ' ').title()

def _clean_fn(raw: str) -> str:
    """'en:skin-conditioning' -> 'Skin Conditioning'"""
    fn = re.sub(r'^[a-z]{2}:', '', raw)
    return fn.replace('-', ' ').title()[:100]

# ── Supabase ─────────────────────────────────────────────────────────────────

async def fetch_existing_inci() -> set:
    """Page through the entire raw_materials table to build a complete dedup set."""
    headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    existing: set = set()
    page_size = 1000
    offset = 0
    async with httpx.AsyncClient(timeout=30) as c:
        while True:
            url = (f"{SUPABASE_URL}/rest/v1/raw_materials"
                   f"?select=inci_name&limit={page_size}&offset={offset}")
            r = await c.get(url, headers=headers)
            if r.status_code != 200:
                print(f"  [warn] Could not fetch existing names at offset {offset}: {r.status_code}")
                break
            batch = r.json()
            if not batch:
                break
            existing.update(row['inci_name'].strip().lower()
                            for row in batch if row.get('inci_name'))
            offset += len(batch)
            if len(batch) < page_size:
                break   # last page
    return existing

async def insert_batch(rows: List[Dict]) -> int:
    """
    Insert rows with ON CONFLICT DO NOTHING semantics for every unique
    constraint (inci_name, cas_number, or any composite).
    'resolution=ignore-duplicates' is PostgREST's way of expressing this —
    it silently skips any row that would violate a unique constraint instead
    of aborting the whole batch.
    """
    url = f"{SUPABASE_URL}/rest/v1/raw_materials"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=ignore-duplicates,return=minimal',
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=rows, headers=headers)
    if r.status_code not in (200, 201, 202, 204):
        print(f"  [warn] Batch error {r.status_code}: {r.text[:400]}")
        return 0
    return len(rows)

async def bulk_insert(rows: List[Dict], existing: set) -> int:
    # Client-side dedup by inci_name (fast, avoids unnecessary round-trips)
    deduped = [r for r in rows
               if r['inci_name'].strip().lower() not in existing
               and len(r['inci_name'].strip()) >= 3]

    # Also deduplicate by cas_number within this batch to avoid intra-batch
    # 23505 violations before they even reach Supabase.
    seen_cas: set = set()
    safe: List[Dict] = []
    for r in deduped:
        cas = r.get('cas_number')
        if cas and cas in seen_cas:
            continue      # duplicate CAS within this source list — skip
        if cas:
            seen_cas.add(cas)
        safe.append(r)

    skipped = len(rows) - len(safe)
    print(f"  Candidates: {len(safe):,} new  |  {skipped:,} skipped (already in DB or dup CAS)")
    if not safe:
        return 0

    total = 0
    n_batches = (len(safe) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(safe), BATCH_SIZE):
        chunk = safe[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        n = await insert_batch(chunk)
        total += n
        for r in chunk:
            existing.add(r['inci_name'].strip().lower())
        pct = batch_num / n_batches * 100
        print(f"  [{pct:5.1f}%] Batch {batch_num}/{n_batches}: +{n:>4} rows | running total {total:,}")
        await asyncio.sleep(BATCH_DELAY)   # 0.5 s between every batch
    return total

# ── Source 1: Open Beauty Facts taxonomy ─────────────────────────────────────

async def fetch_obf() -> Optional[List[Dict]]:
    print(f"\n[1] Downloading Open Beauty Facts ingredient taxonomy ...")
    print(f"    URL: {OBF_URL}")
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.get(OBF_URL, headers={'User-Agent': 'P&D-INCI-Seeder/1.0'})
        if r.status_code != 200:
            print(f"    Failed: HTTP {r.status_code}")
            return None
        print(f"    Downloaded {len(r.content):,} bytes — parsing ...")
        data = r.json()
        rows: List[Dict] = []
        for key, entry in data.items():
            if not isinstance(entry, dict):
                continue

            # ── INCI name: prefer explicit field, fall back to slug ───────────
            name_data = entry.get('name', {})
            inci_raw = (
                name_data.get('en') or
                name_data.get('fr') or
                name_data.get('de') or
                ''
            ).strip()
            if not inci_raw:
                inci_raw = _slug_to_name(key)

            if len(inci_raw) < 2 or len(inci_raw) > 200:
                continue

            # ── INCI description → use as function category ────────────────
            desc_data = entry.get('inci_description', {})
            desc = (desc_data.get('en') or '').strip()[:100]

            fn_data = entry.get('inci_functions', {})
            fn_raw = (fn_data.get('en') or '').strip()
            if fn_raw:
                fn_parts = [_clean_fn(f.strip()) for f in fn_raw.split(',')]
                category = ', '.join(fn_parts)[:100]
            elif desc:
                category = desc[:100]
            else:
                category = 'Cosmetic Ingredient'

            # ── CAS number (not in OBF taxonomy, left blank) ────────────────
            rows.append(_row(inci_raw, inci_raw, '', category))

        print(f"    Parsed {len(rows):,} ingredients")
        return rows
    except Exception as e:
        print(f"    Error: {e}")
        return None

# ── Source 2: Embedded curated list (~600 ingredients) ───────────────────────

def embedded_rows() -> List[Dict]:
    R = _row
    return [
        # ── Water / Solvents ─────────────────────────────────────────────────
        R('Water (Purified)', 'Aqua', '7732-18-5', 'Solvent', 0.01),
        R('Ethanol 96%', 'Alcohol', '64-17-5', 'Solvent', 1.20),
        R('SD Alcohol 40', 'Alcohol Denat.', '64-17-5', 'Solvent', 1.50),
        R('Isopropyl Alcohol', 'Isopropyl Alcohol', '67-63-0', 'Solvent', 1.00),
        R('Butylene Glycol', 'Butylene Glycol', '107-88-0', 'Solvent/Humectant', 4.00),
        R('Pentylene Glycol', 'Pentylene Glycol', '5765-44-6', 'Solvent/Humectant', 8.00),
        R('Dipropylene Glycol', 'Dipropylene Glycol', '25265-71-8', 'Solvent/Humectant', 3.00),
        R('Hexylene Glycol', 'Hexylene Glycol', '107-41-5', 'Solvent/Humectant', 3.50),
        # ── Humectants ───────────────────────────────────────────────────────
        R('Glycerin (Kosher)', 'Glycerin', '56-81-5', 'Humectant', 2.00),
        R('Sodium Hyaluronate (LMW)', 'Sodium Hyaluronate', '9067-32-7', 'Humectant', 250.00),
        R('Panthenol DL-', 'Panthenol', '81-13-0', 'Humectant', 20.00),
        R('Sodium PCA', 'Sodium PCA', '28874-51-3', 'Humectant', 18.00),
        R('Betaine Anhydrous', 'Betaine', '107-43-7', 'Humectant', 5.00),
        R('Trehalose', 'Trehalose', '99-20-7', 'Humectant', 15.00),
        R('Allantoin', 'Allantoin', '97-59-6', 'Humectant/Soothing', 12.00),
        R('Urea (Cosmetic Grade)', 'Urea', '57-13-6', 'Humectant', 3.00),
        R('Sorbitol 70%', 'Sorbitol', '50-70-4', 'Humectant', 1.50),
        R('Propylene Glycol', 'Propylene Glycol', '57-55-6', 'Humectant', 2.50),
        R('Erythritol', 'Erythritol', '149-32-6', 'Humectant', 8.00),
        R('Mannitol', 'Mannitol', '69-65-8', 'Humectant', 5.00),
        R('Xylitol', 'Xylitol', '87-99-0', 'Humectant', 6.00),
        R('Inositol', 'Inositol', '87-89-8', 'Humectant', 12.00),
        R('Sodium Lactate', 'Sodium Lactate', '72-17-3', 'Humectant', 4.00),
        # ── Whitening Actives ─────────────────────────────────────────────────
        R('Niacinamide BP', 'Niacinamide', '98-92-0', 'Whitening Active', 15.00),
        R('Alpha-Arbutin', 'Alpha-Arbutin', '84380-01-8', 'Whitening Active', 180.00),
        R('Beta-Arbutin', 'Arbutin', '497-76-7', 'Whitening Active', 30.00),
        R('Kojic Acid', 'Kojic Acid', '501-30-4', 'Whitening Active', 35.00),
        R('Ascorbic Acid L-C', 'Ascorbic Acid', '50-81-7', 'Whitening Active', 8.00),
        R('Sodium Ascorbyl Phosphate', 'Sodium Ascorbyl Phosphate', '66170-10-3', 'Whitening Active', 45.00),
        R('Magnesium Ascorbyl Phosphate', 'Magnesium Ascorbyl Phosphate', '113170-55-1', 'Whitening Active', 55.00),
        R('Ascorbyl Glucoside', 'Ascorbyl Glucoside', '129499-78-1', 'Whitening Active', 90.00),
        R('Ascorbyl Tetraisopalmitate', 'Ascorbyl Tetraisopalmitate', '183476-82-6', 'Whitening Active', 120.00),
        R('3-O-Ethyl Ascorbic Acid', '3-O-Ethyl Ascorbic Acid', '86404-04-8', 'Whitening Active', 150.00),
        R('Tranexamic Acid', 'Tranexamic Acid', '1197-18-8', 'Whitening Active', 60.00),
        R('Azelaic Acid', 'Azelaic Acid', '123-99-9', 'Whitening Active', 25.00),
        R('4-Butylresorcinol', '4-Butylresorcinol', '18979-61-8', 'Whitening Active', 350.00),
        R('Glabridin', 'Glabridin', '59870-68-7', 'Whitening Active', 800.00),
        R('Glutathione', 'Glutathione', '70-18-8', 'Whitening / Antioxidant', 300.00),
        R('Ferulic Acid', 'Ferulic Acid', '1135-24-6', 'Antioxidant / Whitening', 30.00),
        # ── Anti-aging Actives ────────────────────────────────────────────────
        R('Retinol (Oil)', 'Retinol', '68-26-8', 'Anti-aging Active', 500.00),
        R('Retinyl Palmitate', 'Retinyl Palmitate', '79-81-2', 'Anti-aging Active', 80.00),
        R('Retinyl Acetate', 'Retinyl Acetate', '127-47-9', 'Anti-aging Active', 90.00),
        R('Bakuchiol', 'Bakuchiol', '10309-37-2', 'Anti-aging Active', 250.00),
        R('Adenosine', 'Adenosine', '58-61-7', 'Anti-aging Active', 80.00),
        R('Argireline Solution 10%', 'Acetyl Hexapeptide-3', '616204-22-9', 'Anti-aging Active', 120.00),
        R('Resveratrol', 'Resveratrol', '501-36-0', 'Anti-aging Active', 200.00),
        R('Ceramide NP', 'Ceramide NP', '100403-19-8', 'Anti-aging Active', 300.00),
        R('Ceramide AP', 'Ceramide AP', '18396-21-1', 'Anti-aging Active', 320.00),
        R('Palmitoyl Tripeptide-1', 'Palmitoyl Tripeptide-1', '147732-56-7', 'Anti-aging Active', 450.00),
        R('Palmitoyl Tetrapeptide-7', 'Palmitoyl Tetrapeptide-7', '221227-05-0', 'Anti-aging Active', 500.00),
        R('Coenzyme Q10', 'Ubiquinone', '303-98-0', 'Anti-aging Active', 200.00),
        R('Madecassoside', 'Madecassoside', '34540-22-2', 'Soothing / Anti-aging', 200.00),
        R('Asiaticoside', 'Asiaticoside', '16830-15-2', 'Soothing / Anti-aging', 150.00),
        R('Beta-Glucan', 'Beta-Glucan', '9041-22-9', 'Soothing / Immune', 60.00),
        # ── Emollients / Esters ──────────────────────────────────────────────
        R('Squalane (Plant)', 'Squalane', '111-01-3', 'Emollient', 18.00),
        R('Caprylic/Capric Triglyceride', 'Caprylic/Capric Triglyceride', '65381-09-1', 'Emollient', 4.00),
        R('Isopropyl Myristate', 'Isopropyl Myristate', '110-27-0', 'Emollient', 3.50),
        R('Isopropyl Palmitate', 'Isopropyl Palmitate', '142-91-6', 'Emollient', 3.00),
        R('Ethylhexyl Palmitate', 'Ethylhexyl Palmitate', '29806-73-3', 'Emollient', 4.00),
        R('Ethylhexyl Stearate', 'Ethylhexyl Stearate', '22047-49-0', 'Emollient', 4.50),
        R('C12-15 Alkyl Benzoate', 'C12-15 Alkyl Benzoate', '68411-27-8', 'Emollient', 5.00),
        R('Dicaprylyl Carbonate', 'Dicaprylyl Carbonate', '1680-31-5', 'Emollient', 7.00),
        R('Coco Caprylate/Caprate', 'Coco-Caprylate/Caprate', '90854-36-7', 'Emollient', 5.50),
        R('Isononyl Isononanoate', 'Isononyl Isononanoate', '42131-25-9', 'Emollient', 4.50),
        # ── Emollients / Oils ─────────────────────────────────────────────────
        R('Jojoba Oil', 'Simmondsia Chinensis Seed Oil', '61789-91-1', 'Emollient / Oil', 30.00),
        R('Argan Oil', 'Argania Spinosa Kernel Oil', '223748-82-1', 'Emollient / Oil', 80.00),
        R('Rosehip Oil', 'Rosa Canina Fruit Oil', '84603-93-0', 'Emollient / Oil', 60.00),
        R('Sweet Almond Oil', 'Prunus Amygdalus Dulcis Oil', '8013-76-1', 'Emollient / Oil', 15.00),
        R('Sunflower Oil', 'Helianthus Annuus Seed Oil', '8001-21-6', 'Emollient / Oil', 4.00),
        R('Coconut Oil', 'Cocos Nucifera Oil', '8001-31-8', 'Emollient / Oil', 8.00),
        R('Avocado Oil', 'Persea Gratissima Oil', '8024-32-6', 'Emollient / Oil', 20.00),
        R('Castor Oil', 'Ricinus Communis Seed Oil', '8001-79-4', 'Emollient / Oil', 6.00),
        R('Marula Oil', 'Sclerocarya Birrea Seed Oil', '223950-79-6', 'Emollient / Oil', 90.00),
        R('Camellia Oil', 'Camellia Sinensis Seed Oil', '68916-73-4', 'Emollient / Oil', 25.00),
        R('Grapeseed Oil', 'Vitis Vinifera Seed Oil', '85594-37-2', 'Emollient / Oil', 10.00),
        R('Hemp Seed Oil', 'Cannabis Sativa Seed Oil', '68956-68-3', 'Emollient / Oil', 15.00),
        # ── Silicones ─────────────────────────────────────────────────────────
        R('Dimethicone 350 cSt', 'Dimethicone', '9006-65-9', 'Emollient / Silicone', 6.00),
        R('Cyclopentasiloxane', 'Cyclopentasiloxane', '541-02-6', 'Emollient / Silicone', 8.00),
        R('Phenyl Trimethicone', 'Phenyl Trimethicone', '2116-84-9', 'Emollient / Silicone', 15.00),
        R('Dimethiconol', 'Dimethiconol', '31692-79-2', 'Emollient / Silicone', 10.00),
        R('Amodimethicone', 'Amodimethicone', '71750-79-3', 'Conditioning / Silicone', 12.00),
        # ── Waxes ─────────────────────────────────────────────────────────────
        R('Beeswax (White)', 'Cera Alba', '8012-89-3', 'Wax / Emollient', 12.00),
        R('Candelilla Wax', 'Euphorbia Cerifera Cera', '8006-44-8', 'Wax', 18.00),
        R('Carnauba Wax', 'Copernicia Cerifera Cera', '8015-86-9', 'Wax', 25.00),
        R('Stearic Acid', 'Stearic Acid', '57-11-4', 'Emulsifier / Thickener', 2.50),
        R('Petrolatum (White)', 'Petrolatum', '8009-03-8', 'Emollient', 3.00),
        R('Mineral Oil (Light)', 'Paraffinum Liquidum', '8012-95-1', 'Emollient', 2.00),
        # ── Surfactants ───────────────────────────────────────────────────────
        R('Sodium Lauryl Sulfate', 'Sodium Lauryl Sulfate', '151-21-3', 'Surfactant (Anionic)', 3.00),
        R('SLES 70%', 'Sodium Laureth Sulfate', '9004-82-4', 'Surfactant (Anionic)', 2.00),
        R('Cocamidopropyl Betaine 30%', 'Cocamidopropyl Betaine', '61789-40-0', 'Surfactant (Amphoteric)', 3.50),
        R('Sodium Cocoyl Isethionate', 'Sodium Cocoyl Isethionate', '61789-32-0', 'Surfactant (Anionic)', 8.00),
        R('Decyl Glucoside', 'Decyl Glucoside', '68515-73-1', 'Surfactant (Nonionic)', 7.00),
        R('Coco Glucoside', 'Coco Glucoside', '68515-73-1', 'Surfactant (Nonionic)', 8.00),
        R('Lauryl Glucoside', 'Lauryl Glucoside', '110615-47-9', 'Surfactant (Nonionic)', 7.50),
        R('Sodium Cocoyl Glutamate', 'Sodium Cocoyl Glutamate', '68187-30-4', 'Surfactant (Anionic)', 12.00),
        R('Sodium Lauroyl Glutamate', 'Sodium Lauroyl Glutamate', '29923-31-7', 'Surfactant (Anionic)', 14.00),
        R('Disodium Cocoamphodiacetate', 'Disodium Cocoamphodiacetate', '68650-39-5', 'Surfactant (Amphoteric)', 9.00),
        # ── Emulsifiers ───────────────────────────────────────────────────────
        R('Glyceryl Stearate SE', 'Glyceryl Stearate', '31566-31-1', 'Emulsifier', 5.00),
        R('Cetearyl Alcohol', 'Cetearyl Alcohol', '67762-27-0', 'Emulsifier / Fatty Alcohol', 3.50),
        R('Cetyl Alcohol', 'Cetyl Alcohol', '36653-82-4', 'Emulsifier / Fatty Alcohol', 3.00),
        R('Polysorbate 20', 'Polysorbate 20', '9005-64-5', 'Emulsifier', 4.00),
        R('Polysorbate 80', 'Polysorbate 80', '9005-65-6', 'Emulsifier', 4.50),
        R('Sorbitan Stearate', 'Sorbitan Stearate', '1338-41-6', 'Emulsifier', 5.50),
        R('Lecithin (Sunflower)', 'Lecithin', '8002-43-5', 'Emulsifier', 12.00),
        R('PEG-100 Stearate', 'PEG-100 Stearate', '9004-99-3', 'Emulsifier', 6.00),
        R('Ceteareth-20', 'Ceteareth-20', '68439-49-6', 'Emulsifier', 5.00),
        R('Behentrimonium Methosulfate', 'Behentrimonium Methosulfate', '81646-13-1', 'Emulsifier / Conditioning', 15.00),
        R('PEG-40 Castor Oil', 'PEG-40 Castor Oil', '61791-12-6', 'Emulsifier / Solubilizer', 6.00),
        # ── Thickeners ────────────────────────────────────────────────────────
        R('Carbomer 980', 'Carbomer', '9003-01-4', 'Thickener / Gelling', 12.00),
        R('Acrylates/C10-30 Crosspolymer', 'Acrylates/C10-30 Alkyl Acrylate Crosspolymer', '9062-04-8', 'Thickener / Gelling', 14.00),
        R('Xanthan Gum', 'Xanthan Gum', '11138-66-2', 'Thickener / Gelling', 8.00),
        R('Hydroxyethylcellulose', 'Hydroxyethylcellulose', '9004-62-0', 'Thickener / Gelling', 10.00),
        R('HPMC (Methocel)', 'Hydroxypropyl Methylcellulose', '9004-65-3', 'Thickener / Gelling', 11.00),
        R('Sclerotium Gum', 'Sclerotium Gum', '39464-87-4', 'Thickener / Gelling', 25.00),
        R('Sodium Alginate', 'Sodium Alginate', '9005-38-3', 'Thickener / Gelling', 10.00),
        R('Carrageenan', 'Carrageenan', '9000-07-1', 'Thickener / Gelling', 15.00),
        # ── Preservatives ─────────────────────────────────────────────────────
        R('Phenoxyethanol', 'Phenoxyethanol', '122-99-6', 'Preservative', 8.00),
        R('Ethylhexylglycerin', 'Ethylhexylglycerin', '70445-33-9', 'Preservative', 25.00),
        R('Benzyl Alcohol', 'Benzyl Alcohol', '100-51-6', 'Preservative', 5.00),
        R('Sodium Benzoate', 'Sodium Benzoate', '532-32-1', 'Preservative', 2.50),
        R('Potassium Sorbate', 'Potassium Sorbate', '24634-61-5', 'Preservative', 3.00),
        R('Caprylyl Glycol', 'Caprylyl Glycol', '1117-86-8', 'Preservative', 18.00),
        R('1,2-Hexanediol', '1,2-Hexanediol', '6920-22-5', 'Preservative', 15.00),
        R('Chlorphenesin', 'Chlorphenesin', '104-29-0', 'Preservative', 20.00),
        R('Sodium Dehydroacetate', 'Sodium Dehydroacetate', '4418-26-2', 'Preservative', 8.00),
        R('Methylparaben', 'Methylparaben', '99-76-3', 'Preservative', 4.00),
        R('Propylparaben', 'Propylparaben', '94-13-3', 'Preservative', 5.00),
        R('Gluconolactone', 'Gluconolactone', '90-80-2', 'Preservative / AHA', 8.00),
        # ── Antioxidants ──────────────────────────────────────────────────────
        R('Tocopherol (Vitamin E)', 'Tocopherol', '1406-18-4', 'Antioxidant', 40.00),
        R('Tocopheryl Acetate', 'Tocopheryl Acetate', '58-95-7', 'Antioxidant', 20.00),
        R('BHT', 'BHT', '128-37-0', 'Antioxidant', 8.00),
        R('Ascorbyl Palmitate', 'Ascorbyl Palmitate', '137-66-6', 'Antioxidant', 25.00),
        R('Disodium EDTA', 'Disodium EDTA', '139-33-3', 'Chelating Agent', 4.00),
        # ── pH Adjusters ──────────────────────────────────────────────────────
        R('Citric Acid (Anhydrous)', 'Citric Acid', '77-92-9', 'pH Adjuster', 2.00),
        R('Sodium Hydroxide 50%', 'Sodium Hydroxide', '1310-73-2', 'pH Adjuster', 0.80),
        R('Triethanolamine 99%', 'Triethanolamine', '102-71-6', 'pH Adjuster', 3.00),
        R('Lactic Acid 88%', 'Lactic Acid', '50-21-5', 'pH Adjuster / AHA', 3.50),
        R('Arginine', 'Arginine', '74-79-3', 'Amino Acid / pH Adjuster', 15.00),
        R('Sodium Citrate', 'Sodium Citrate', '68-04-2', 'pH Buffering', 2.50),
        # ── Exfoliants ────────────────────────────────────────────────────────
        R('Glycolic Acid 70%', 'Glycolic Acid', '79-14-1', 'Exfoliant (AHA)', 12.00),
        R('Salicylic Acid', 'Salicylic Acid', '69-72-7', 'Exfoliant (BHA)', 10.00),
        R('Mandelic Acid', 'Mandelic Acid', '90-64-2', 'Exfoliant (AHA)', 18.00),
        R('Malic Acid', 'Malic Acid', '6915-15-7', 'Exfoliant (AHA)', 6.00),
        R('Lactobionic Acid', 'Lactobionic Acid', '96-82-2', 'Exfoliant (PHA)', 25.00),
        # ── UV Filters ────────────────────────────────────────────────────────
        R('Zinc Oxide (Nano-free)', 'Zinc Oxide', '1314-13-2', 'UV Filter (Inorganic)', 10.00),
        R('Titanium Dioxide (Coated)', 'Titanium Dioxide', '13463-67-7', 'UV Filter (Inorganic)', 8.00),
        R('Octinoxate (OMC)', 'Ethylhexyl Methoxycinnamate', '5466-77-3', 'UV Filter (Organic)', 12.00),
        R('Tinosorb S (BEMT)', 'Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine', '187393-00-6', 'UV Filter (Organic)', 80.00),
        R('Avobenzone', 'Butyl Methoxydibenzoylmethane', '70356-09-1', 'UV Filter (Organic)', 15.00),
        R('Octocrylene', 'Octocrylene', '6197-30-4', 'UV Filter (Organic)', 12.00),
        R('Homosalate', 'Homosalate', '118-56-9', 'UV Filter (Organic)', 8.00),
        R('Octisalate (EHS)', 'Ethylhexyl Salicylate', '118-60-5', 'UV Filter (Organic)', 9.00),
        # ── Minerals ──────────────────────────────────────────────────────────
        R('Kaolin Clay', 'Kaolin', '1332-58-7', 'Mineral / Absorbent', 2.00),
        R('Talc (Cosmetic Grade)', 'Talc', '14807-96-6', 'Mineral / Absorbent', 1.50),
        R('Silica (Amorphous)', 'Silica', '7631-86-9', 'Mineral / Absorbent', 8.00),
        R('Mica (Cosmetic Grade)', 'Mica', '12001-26-2', 'Mineral / Colorant', 5.00),
        R('Iron Oxide Red', 'Iron Oxides (CI 77491)', '1309-37-1', 'Colorant', 5.00),
        R('Iron Oxide Yellow', 'Iron Oxides (CI 77492)', '51274-00-1', 'Colorant', 5.00),
        R('Iron Oxide Black', 'Iron Oxides (CI 77499)', '1317-61-9', 'Colorant', 5.00),
        # ── Botanical Extracts ────────────────────────────────────────────────
        R('Aloe Vera Gel', 'Aloe Barbadensis Leaf Juice', '85507-69-3', 'Botanical Extract', 5.00),
        R('Centella Asiatica Extract', 'Centella Asiatica Extract', '84696-21-9', 'Botanical Extract', 30.00),
        R('Green Tea Extract', 'Camellia Sinensis Leaf Extract', '84650-60-2', 'Botanical Extract', 25.00),
        R('Licorice Root Extract', 'Glycyrrhiza Glabra Root Extract', '68916-91-6', 'Botanical Extract', 20.00),
        R('Chamomile Extract', 'Matricaria Recutita Flower Extract', '84082-60-0', 'Botanical Extract', 15.00),
        R('Bifida Ferment Lysate', 'Bifida Ferment Lysate', '', 'Biotech / Probiotic', 80.00),
        R('Galactomyces Ferment Filtrate', 'Galactomyces Ferment Filtrate', '', 'Biotech / Probiotic', 100.00),
        # ── Proteins & Conditioning ───────────────────────────────────────────
        R('Hydrolyzed Collagen', 'Hydrolyzed Collagen', '9015-54-7', 'Protein / Conditioning', 30.00),
        R('Hydrolyzed Keratin', 'Hydrolyzed Keratin', '69430-36-0', 'Protein / Conditioning', 40.00),
        R('Hydrolyzed Silk', 'Hydrolyzed Silk', '96690-41-4', 'Protein / Conditioning', 60.00),
        R('Polyquaternium-10', 'Polyquaternium-10', '68610-92-4', 'Conditioning / Film Former', 8.00),
        R('Behentrimonium Chloride', 'Behentrimonium Chloride', '17301-53-0', 'Conditioning', 8.00),
        R('Colloidal Oatmeal', 'Avena Sativa Kernel Flour', '977069-08-1', 'Soothing / Emollient', 12.00),
    ]

# ── main ─────────────────────────────────────────────────────────────────────

async def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        sys.exit(1)

    print("=" * 60)
    print("P&D Cosmetic Raw Materials - Global INCI Seeder")
    print("=" * 60)

    print("\nFetching existing INCI names from DB ...")
    existing = await fetch_existing_inci()
    print(f"  Currently in DB: {len(existing)} entries")

    # Source 1: Open Beauty Facts
    rows = await fetch_obf()
    source = "Open Beauty Facts taxonomy"

    if not rows:
        print("\n[2] OBF unavailable - using embedded curated list ...")
        rows = embedded_rows()
        source = "Embedded curated list"

    print(f"\nSource: {source}")
    print(f"Total rows from source: {len(rows):,}")
    inserted = await bulk_insert(rows, existing)

    # ── Final verified count ──────────────────────────────────────────────────
    count_headers = {**{'Prefer': 'count=exact'}, 'apikey': SUPABASE_KEY,
                     'Authorization': f'Bearer {SUPABASE_KEY}'}
    async with httpx.AsyncClient(timeout=15) as c:
        cr = await c.get(f"{SUPABASE_URL}/rest/v1/raw_materials?select=id&limit=0",
                         headers=count_headers)
    db_total = cr.headers.get('content-range', '*/0').split('/')[-1]

    print("\n" + "=" * 60)
    print(f"Inserted this run : {inserted:,} new materials")
    print(f"Verified DB total : {db_total} rows in raw_materials")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(main())
