---
name: data-quality-assessment
description: 'Assesses and scores LCA dataset quality using Pedigree/DQI/DQR methods. Triggers on "data quality", "DQI", "DQR", "Pedigree", "representativeness", "数据质量", "代表性评估", or comparisons between dataset reliability. Does NOT search data — use lca-search for that.'
---

# Data Quality Assessment

Assess LCA dataset quality using standardized scoring frameworks: Pedigree Matrix, PEF DQR, and ILCD DQI.

## Scoring Frameworks

### 1. Pedigree Matrix (ecoinvent / Weidema et al.)

The most widely used DQI system. 5 indicators, each scored 1 (best) to 5 (worst):

| Score | Reliability | Completeness | Temporal | Geographical | Technological |
|-------|------------|-------------|----------|-------------|---------------|
| **1** | Verified data based on measurements | Representative of all relevant sites | < 3 years difference | Data from area under study | Data from enterprises/processes under study |
| **2** | Verified data partly based on assumptions | Representative of > 50% of sites | < 6 years difference | Average data from larger area | Data from similar but not identical processes |
| **3** | Non-verified data partly based on assumptions | Representative of only some sites | < 10 years difference | Data from area with similar conditions | Data from processes with same technology |
| **4** | Qualified estimate | Representative of one site | < 15 years difference | Data from area with slightly similar conditions | Data from related processes, same technology |
| **5** | Non-qualified estimate | Unknown or incomplete | Age unknown or > 15 years | Unknown or very different area | Data from related processes, different technology |

**Aggregated Score (practitioner convention):** Arithmetic or geometric mean of 5 indicators. Note: ecoinvent officially uses pedigree scores to derive uncertainty factors (variance), not a single quality score. The thresholds below are a widely-used practitioner simplification:
- ≤ 2.0: High quality
- 2.0–3.0: Acceptable quality
- 3.0–4.0: Low quality — consider alternatives
- \> 4.0: Very low quality — should be replaced

### 2. PEF Data Quality Rating (EU Product Environmental Footprint)

Required for EU PEF studies and increasingly for CBAM. 4 indicators:

| Score | TeR (Technological) | GR (Geographical) | TiR (Temporal) | P (Precision) |
|-------|--------------------|--------------------|----------------|---------------|
| **1** | Exact technology mix | Exact geography | Reference year ± 2 years | Measured/calculated, verified |
| **2** | Similar technology | Country level | Reference year ± 4 years | Measured/calculated, partly verified |
| **3** | Similar but different tech | Continent level | Reference year ± 6 years | Measured/calculated, not verified |
| **4** | Based on related processes | Global average | Reference year ± 8 years | Documented estimate |
| **5** | Unknown technology | Unknown geography | Reference year ± 10+ years | Non-documented estimate |

**DQR = (TeR + GR + TiR + P) / 4**

| DQR Score | Quality Level | PEF Context |
|-----------|--------------|-------------|
| ≤ 1.5 | Excellent | Meets company-specific dataset requirement |
| 1.6–2.5 | Good | Maximum for individual company-specific data items |
| 2.5–3.0 | Acceptable | Meets secondary dataset requirement |
| 3.0–4.0 | Low | May require justification |
| \> 4.0 | Insufficient | Should be replaced |

*Thresholds based on EU PEF method (Commission Recommendation 2021/2279). Named quality levels are interpretive guidance, not regulatory labels.*

### 3. ILCD Data Quality Indicators

Used in ILCD/LCDN/EPD context. Same 5 dimensions as Pedigree but with different labels:

- **Representativeness** (overall)
- **Methodological appropriateness and consistency**
- **Completeness** (of inventory)
- **Precision/uncertainty**
- **Time representativeness**
- **Geographical representativeness**
- **Technological representativeness**

Rating: Very good / Good / Fair / Poor / Very poor

## Assessment Workflow

### Step 1: Identify the Dataset

What dataset is being assessed? Gather:
- Dataset name and source database
- Reference year of the data
- Geography (country/region)
- Technology description
- Data collection method (measured, calculated, estimated, literature)

### Step 2: Determine Assessment Context

Ask the user:
- **Purpose**: General LCA study? PEF? CBAM? EPD?
- **Target product/process**: What is the dataset representing in their study?
- **Target geography**: Where is the user's product manufactured/used?
- **Target time**: What year is the study for?

### Step 3: Score Each Indicator

For each indicator, explain the reasoning:

```
## Data Quality Assessment: "Steel, converter, unalloyed — CN" (HiQLCD v1.4)

### Pedigree Matrix Scoring

| Indicator | Score | Reasoning |
|-----------|-------|-----------|
| Reliability | 2 | Industry-average data based on Chinese steel association statistics, partially verified |
| Completeness | 2 | Covers major steelmakers, > 60% of national production |
| Temporal | 1 | Data from 2023, study year 2024 — within 3 years |
| Geographical | 1 | Chinese data for Chinese study — exact match |
| Technological | 2 | BOF process data, matches user's supplier (BOF route) |

**Aggregated Score: 1.52** (Geometric mean)
**Quality Level: HIGH** ✅

### PEF DQR Scoring

| TeR | GR | TiR | P | DQR |
|-----|-----|-----|---|-----|
| 2 | 1 | 1 | 2 | **1.50** |

**PEF Quality: EXCELLENT** — Exceeds requirements ✅
```

### Step 4: Comparison (if applicable)

If user is choosing between datasets, score both and compare:

```
## Comparison

| Indicator | HiQLCD CN Steel | ecoinvent RER Steel |
|-----------|----------------|---------------------|
| Temporal | 1 (2023) | 2 (2020) |
| Geographical | 1 (CN → CN) | 3 (Europe → CN) |
| Technological | 2 (BOF avg) | 2 (BOF avg) |
| Pedigree Score | **1.52** | **2.29** |
| Recommendation | ✅ **Preferred** | Acceptable backup |

**Recommendation:** Use HiQLCD CN Steel — better geographical and temporal representativeness for a Chinese manufacturing study.
```

### Step 5: Report

Generate a summary with:
- Dataset identification
- Assessment framework used (Pedigree / PEF DQR / ILCD)
- Score per indicator with reasoning
- Overall quality level
- Recommendation (use as-is / use with caution / replace)
- Suggested alternatives if quality is low

## Common Scenarios

### "Is Ecoinvent data good enough for my Chinese study?"

Assess geographical representativeness:
- Ecoinvent `RER` (Europe) or `GLO` (Global) data for a China-specific study → GR score 3-4
- Recommend checking HiQLCD or TianGong for Chinese-specific alternatives
- If no Chinese data exists, document the proxy and its limitations

### "My data is 8 years old, is it still valid?"

Temporal representativeness:
- For stable technologies (basic metals, chemicals): 8 years may be acceptable (score 3)
- For fast-changing sectors (electronics, batteries, renewables): 8 years is problematic (score 4-5)
- Always check if newer versions of the dataset exist

### "Which dataset should I use for CBAM reporting?"

PEF DQR is mandatory:
- DQR must be ≤ 3.0 for CBAM transitional period
- Prioritize: actual plant data (score 1) > country average (score 2) > default values (score 4-5)
- CBAM default values are intentionally penalizing — always try to use better data

## Important Notes

- Always state which framework you're using (Pedigree / PEF DQR / ILCD)
- Scoring involves judgment — explain reasoning for each score
- A low score doesn't mean the data is wrong, just that representativeness is limited
- For PEF/CBAM, the DQR formula and thresholds are regulatory requirements, not suggestions
- Offer to search for alternative datasets if quality is insufficient
