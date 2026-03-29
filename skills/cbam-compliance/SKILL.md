---
name: cbam-compliance
description: 'Provides EU CBAM (Carbon Border Adjustment Mechanism) compliance guidance — product scope, reporting requirements, default values, and embedded emissions calculation. Triggers on "CBAM", "carbon border", "碳边境", "碳关税", "EU carbon tax", "embedded emissions", or questions about CBAM reporting and calculations.'
---

# CBAM Compliance Guide

EU Carbon Border Adjustment Mechanism — product scope, reporting requirements, emission calculations, and data needs.

## CBAM Overview

CBAM is the EU's carbon border tax on imported goods. It requires importers to report (and eventually pay for) the embedded carbon emissions in certain products.

**Timeline:**
- **2023 Oct – 2025 Dec**: Transitional period (reporting only, no payments)
- **2026 Jan onwards**: Definitive period (certificates must be purchased)
- **2026–2034**: Phase-in aligned with EU ETS free allowance phase-out

## Product Scope (Annex I)

### Covered Sectors and CN Codes

| Sector | Key Products | CN Codes (examples) |
|--------|-------------|---------------------|
| **Iron & Steel** | Crude steel, flat/long products, pipes, fittings, rails | 7206-7229, 7301-7326 |
| **Aluminium** | Unwrought aluminium, bars, profiles, sheets, foil | 7601-7616 |
| **Cement** | Clinker, portland cement, aluminous cement | 2507, 2523 |
| **Fertilizers** | Urea, ammonium nitrate, NPK, superphosphates | 3102-3105 |
| **Electricity** | Imported electricity | 2716 |
| **Hydrogen** | Hydrogen gas | 2804 10 00 |

### Is My Product Covered?

Decision tree:
1. Does the product fall under one of the 6 sectors above?
2. Check the specific CN code against Annex I of Regulation (EU) 2023/956
3. **Downstream products** (e.g., screws made from steel) are covered if listed
4. **Mixtures/alloys** are covered if the base material is listed

If user provides a product, identify the relevant CN code and confirm coverage.

## Emission Calculation

### Two Types of Emissions

| Type | Definition | Example |
|------|-----------|---------|
| **Direct emissions** | From the production process itself | CO2 from cement kiln, blast furnace |
| **Indirect emissions** | From electricity consumed in production | Electricity for aluminium smelting |

**Which products need indirect emissions?**
- Aluminium: YES (electricity-intensive)
- Cement: NO (direct emissions dominate)
- Iron & Steel: depends on route (EAF = yes, BOF = less significant)
- Fertilizers: NO for transitional period
- Hydrogen: depends on production route

### Calculation Formula

**Specific embedded emissions (SEE) = Direct + Indirect**

```
Direct SEE = (Direct emissions from process) / (Mass of product)
           = tonnes CO2e / tonne product

Indirect SEE = (Electricity consumed × Emission factor) / (Mass of product)
             = (MWh × tCO2e/MWh) / tonne product
```

### Emission Factor Hierarchy (Data Source Priority)

| Priority | Source | DQR | Notes |
|----------|--------|-----|-------|
| 1 | **Actual plant data** (monitored) | Best | Required from 2026 for definitive period |
| 2 | **Verified third-party data** | Good | Accepted during transitional period |
| 3 | **Country average** | Acceptable | E.g., Chinese grid factor for electricity |
| 4 | **CBAM default values** | Penalizing | Published by EU Commission, intentionally high |

⚠️ **CBAM default values are punishment values** — they represent the worst-performing installations in the EU. Always try to provide actual or country-average data.

### Default Values (Selected)

| Product | Benchmark (tCO2/t) | China Default (tCO2/t) | Notes |
|---------|--------------------|-----------------------|-------|
| Crude steel (BF-BOF) | 1.370 | ~3.167 | Country defaults are higher than benchmarks |
| Crude steel (DRI-EAF) | 0.481 | — | Direct reduced iron route |
| Crude steel (Scrap-EAF) | 0.072 | — | Scrap-based, very low |
| Aluminium (primary) | ~4.5 (direct) | ~8.0 (incl. indirect) | Indirect emissions dominant |
| Aluminium (secondary) | ~0.5 | — | Recycled |
| Cement (clinker) | ~0.85 | — | Mainly process emissions |
| Urea | ~1.6 | — | Process + energy |

*Benchmark values from EU Implementing Regulation 2025/2621 (definitive period). Country-specific defaults vary and are published separately. Always check the latest EU Commission publication.*

## Reporting Requirements

### Transitional Period (Current)

Quarterly CBAM reports must include:
1. **Product identification**: CN code, description, country of origin
2. **Quantity**: Mass in tonnes
3. **Total embedded emissions**: tCO2e
4. **Specific embedded emissions**: tCO2e per tonne
5. **Data source**: Actual / default / other
6. **Carbon price paid**: If any carbon price was paid in the country of origin (e.g., China ETS)

### Data Collection from Suppliers

What to ask your supplier:
1. Production process route (e.g., BOF vs EAF for steel)
2. Annual production volume
3. Annual direct CO2 emissions (from process + fuel combustion)
4. Annual electricity consumption (MWh)
5. Electricity source (grid / renewable / specific mix)
6. Any carbon price already paid (e.g., China ETS allowances)

### Carbon Price Deduction

If a carbon price has been paid in the country of origin:
- China ETS covers power generation sector
- Some steel/cement/aluminium may be covered in future
- Deductible amount = (carbon price paid × embedded emissions)
- Must provide proof of payment

## LCA Data Needs for CBAM

### What to Search For

When helping users with CBAM, search for:

1. **Production process data**: `search steel BOF production` with location matching country of origin
2. **Electricity emission factor**: `search electricity grid mix` for the specific country
3. **Fuel combustion factors**: `search natural gas combustion` if needed
4. **Transport emissions**: Usually NOT included in CBAM (only production emissions)

### Connecting to LCA Search

After identifying the user's products and CBAM scope:
1. Use `lca-search` to find relevant emission factor datasets
2. Use `data-quality-assessment` to verify data quality meets CBAM requirements
3. Prioritize: country-specific data > regional average > CBAM default values

## Workflow

### User asks "Does my product fall under CBAM?"

1. Ask what product they're exporting to the EU
2. Identify the CN code
3. Check against Annex I scope
4. Report: covered / not covered, with specific CN code reference

### User asks "What data do I need for CBAM?"

1. Identify which sector and products
2. List required data points (see Reporting Requirements above)
3. Provide a data collection template for their supplier
4. Suggest searching for backup emission factors in case supplier data is unavailable

### User asks "Help me calculate CBAM emissions"

1. Gather: product type, production route, production volume, direct emissions, electricity consumption
2. Calculate specific embedded emissions using the formula
3. Score data quality using PEF DQR framework
4. Compare with CBAM default values — if user's data is lower, they save money

## Important Notes

- CBAM regulations are evolving — always note that guidance is based on current rules
- Default values change with implementing regulation updates
- For definitive period (2026+), actual monitored data will be required
- CBAM only covers production emissions, not use-phase or end-of-life
- Suggest users consult their customs/compliance team for official filings
