# Project: Cosmetic P&D Intelligence Suite (R&D Command Center)

## Tech Stack Target
- Frontend: Vanilla JS / Tailwind CSS (Clean & Minimal Dark Theme)
- Backend: Python (FastAPI + Playwright)
- Database: Supabase (PostgreSQL)

## Core Features Breakdown

### Phase 1: Multi-Site Modular Scraper & Smart Parser
- [ ] Setup workspace directories (`/frontend` and `/backend`).
- [ ] Design a modular scraper architecture (Strategy Pattern) in the backend to easily support multiple supplier domains in the future.
- [ ] Implement the first scraper module specifically for `myskinrecipes.com` utilizing Playwright to bypass CORS and dynamic content.
- [ ] Implement Regex Parser to sanitize extracted text into standard INCI lists, supporting formats like `Glycerin = 5%`, `Retinol: 0.3%`, or raw text names.

### Phase 2: Formulation Engine (Batch, Costing, Loss & Version Control)
- [ ] Build Formulation Worksheet UI allowing users to input ingredients grouped by Phase (Phase A, B, C, D, etc.).
- [ ] Implement Batch Calculator: Automatically scale % into exact weights in grams/kilograms based on user-defined Target Batch Size.
- [ ] Implement Yield/Loss Factor: Allow users to input an estimated production loss percentage (% Loss) and automatically calculate the required overage weights so the final output matches the target batch size.
- [ ] Implement Real-Time Costing: Fetch `price_per_kg` from the Raw Materials Database and calculate the exact cost of the formulation per kilogram and per batch (accounting for the loss factor).
- [ ] Add Formula Versioning (v1.0, v1.1, v2.0) to track adjustments, iterations, and active raw material shelf-life/lot numbers.

### Phase 3: Regulatory Compliance Engine (Thai FDA & Global Export)
- [ ] Create Regulatory Database Schema based on Thai FDA & ASEAN Cosmetic Directive (ACD) guidelines.
- [ ] Implement Real-Time Compliance Checker:
    - [ ] Flag restricted ingredients if they exceed the maximum allowable % for specific target areas (`face`, `body`, `rinse-off`).
    - [ ] Highlight mandatory warning labels required on packaging based on active ingredients.
- [ ] Implement Export Compliance Matrix: Analyze the INCI list and flag which global markets (EU/UK, ASEAN, US FDA, Canada) allow or ban this exact formula.

### Phase 4: Quality Control & Stability Tracker
- [ ] Create Stability Testing Logs bound to specific formulas and versions.
- [ ] Build Tracking Matrix for multiple storage conditions (Room Temp, 40°C, 45°C, Freeze-Thaw) across periods (Week 1, Month 1, Month 3).
- [ ] Record critical QC parameters: pH value, Viscosity, Color, Odor, and Phase Separation status.
- [ ] Add system notifications/alerts when a formula is due for its next stability checkpoint.

### Phase 5: Manufacturing Sheet & Document Export
- [ ] Build an Automated Label INCI Generator: Automatically sort and format ingredients in descending order of concentration (Descending Order Rule) down to 1% to generate legal-compliant packaging ingredients text instantly.
- [ ] Build a one-click PDF Generator for Manufacturing/Mixing Instruction Sheets (SOPs) organized by Phase (including RPM, Mixing Time, Temp logs).
- [ ] Build a basic template structure to export data ready for the Product Information File (PIF) and Thai FDA registration.