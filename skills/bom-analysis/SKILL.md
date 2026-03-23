---
name: bom-analysis
description: "Use this skill when the user uploads a Bill of Materials (BOM), material list, or product composition table and wants it analyzed. Triggers include: any mention of 'BOM', 'bill of materials', 'material list', '物料清单', '配方表', or when the user uploads an Excel/CSV containing material names, quantities, and units. Also trigger when user asks to 'check my BOM', 'clean up this material list', 'what materials am I missing', or wants to prepare a BOM for LCA data matching. Do NOT trigger for LCA data search — use lca-search instead."
---

# BOM Analysis

Analyze, clean, and prepare Bills of Materials for LCA data matching.

## When to Use

- User uploads an Excel/CSV with materials
- User asks to review, clean, or check a BOM
- User wants to prepare a material list for background data matching
- User asks about material completeness or categorization

## Analysis Workflow

### Step 1: Read and Parse

Read the uploaded file. Identify the key columns:
- **Material name** (may be in Chinese/English, may have aliases)
- **Quantity/Amount** (mass, volume, energy, count)
- **Unit** (kg, g, t, m³, L, kWh, MJ, pcs)
- **Category/Type** (if present)
- **Supplier/Source** (if present)

### Step 2: Structure Analysis

Report a summary table:

```
## BOM Summary

| Item | Value |
|------|-------|
| Total materials | 31 |
| Unique materials | 28 (3 duplicates) |
| Materials with quantity | 29 (2 missing) |
| Unit types | kg (18), m³ (5), kWh (4), pcs (2) |
| Languages detected | Chinese (20), English (11) |
```

### Step 3: Issue Detection

Check for these common problems:

**Duplicates:**
- Same material, different names ("不锈钢304" vs "304不锈钢" vs "Stainless Steel 304")
- Same material, different rows (may need to sum quantities)

**Missing Data:**
- Materials without quantity → flag
- Materials without unit → flag
- Quantities that seem unreasonable (e.g., 0, negative, extremely large)

**Unit Inconsistencies:**
- Mixed units for same material type (some in kg, some in g)
- Ambiguous units (e.g., "个" could be pieces or units)
- Energy vs mass confusion (kWh for a material that should be kg)

**Naming Issues:**
- Overly generic names ("steel", "plastic", "paint") → suggest specifics
- Abbreviations that may be ambiguous
- Mixed language in same column

**Categorization:**
- Classify materials into standard categories:
  - Raw materials (metals, plastics, chemicals)
  - Energy (electricity, natural gas, steam)
  - Transport (tkm, logistics)
  - Packaging (carton, film, pallet)
  - Waste/Emissions (if included)

### Step 4: Cleaning Suggestions

For each issue found, provide specific fix:

```
## Issues Found (7)

### Duplicates (2)
1. Row 5 "304不锈钢" and Row 18 "不锈钢304" → same material, merge to "304 Stainless Steel", sum quantities: 15.2 kg
2. Row 8 "PE膜" and Row 22 "聚乙烯薄膜" → same material (PE film), merge

### Missing Data (2)
3. Row 12 "铜线" — no quantity specified
4. Row 27 "lubricant" — no unit specified (likely kg)

### Generic Names (3)
5. Row 3 "钢" → What kind? Carbon steel? Stainless? Alloy? (carbon footprint differs 2-10x)
6. Row 15 "plastic" → What polymer? PE/PP/PVC/ABS? (suggest checking product spec)
7. Row 20 "paint" → Solvent-based or water-based? (very different emission profiles)
```

### Step 5: LCA Readiness Assessment

Rate the BOM's readiness for LCA data matching:

| Criterion | Status | Note |
|-----------|--------|------|
| Material specificity | 🟡 3 generic names need clarification | |
| Quantity completeness | 🟡 2 materials missing quantities | |
| Unit consistency | 🟢 All units parseable | |
| Duplicate-free | 🔴 2 duplicate pairs found | |
| Category coverage | 🟢 Raw materials + energy + transport covered | |
| **Overall readiness** | **🟡 Needs minor cleanup** | Fix 7 issues, then ready for matching |

### Step 6: Output

Generate a cleaned version of the BOM as Excel/CSV with:
- Duplicates merged
- Units standardized
- Categories assigned
- Issues flagged with comments
- Ready for `lca-search` batch matching

## Material Category Reference

| Category | Examples | Typical Unit |
|----------|----------|-------------|
| Ferrous metals | Carbon steel, stainless steel, cast iron | kg |
| Non-ferrous metals | Aluminum, copper, zinc, brass | kg |
| Plastics & polymers | PE, PP, PVC, ABS, PA, PET | kg |
| Chemicals | Solvents, adhesives, coatings, acids | kg or L |
| Building materials | Concrete, cement, glass, ceramics | kg or m³ |
| Energy | Electricity, natural gas, steam, diesel | kWh, MJ, m³, L |
| Transport | Road, rail, sea, air freight | tkm |
| Packaging | Cardboard, wood pallet, PE film, steel drum | kg |
| Water | Process water, cooling water | m³ or L |
| Waste treatment | Landfill, incineration, recycling | kg |

## Important Notes

- Always ask the user to confirm duplicate merges before applying
- Never guess quantities — flag as missing
- For generic materials, use AskUserQuestion with specific options
- After cleanup, suggest using `lca-search` for batch matching
