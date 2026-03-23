---
name: scope3-guidance
description: "Use this skill when the user asks about Scope 3 emissions, GHG Protocol categorization, carbon footprint scope classification, or supply chain emissions. Triggers include: any mention of 'Scope 3', 'Scope 1 2 3', 'GHG Protocol', 'supply chain emissions', 'upstream emissions', 'downstream emissions', 'value chain', '范围三', '供应链碳排放', '上下游排放', '温室气体核算', 'corporate carbon footprint', 'product carbon footprint'. Also trigger when user asks how to classify their emission sources, what counts as Scope 3, or how to collect Scope 3 data."
---

# Scope 3 Guidance

GHG Protocol Scope 1/2/3 classification, 15 Scope 3 categories, boundary definition, data collection, and calculation methods.

## Scope Overview

| Scope | What it covers | Boundary | Data owner |
|-------|---------------|----------|------------|
| **Scope 1** | Direct emissions from owned/controlled sources | Company operations | Your company |
| **Scope 2** | Indirect emissions from purchased energy | Electricity, heat, steam | Energy supplier |
| **Scope 3** | All other indirect emissions in the value chain | Upstream + downstream | Supply chain partners |

Scope 3 typically accounts for **70–90%** of a company's total carbon footprint.

## Scope 3: 15 Categories

### Upstream (Categories 1–8)

| Cat | Name | Description | Typical Data Sources |
|-----|------|-------------|---------------------|
| **1** | **Purchased goods & services** | Emissions from producing all purchased inputs | Supplier data, LCA databases, spend-based factors |
| **2** | **Capital goods** | Emissions from producing capital equipment | Same as Cat 1, amortized over lifetime |
| **3** | **Fuel- and energy-related** (not in Scope 1/2) | Upstream of fuels, T&D losses | Well-to-tank factors, grid loss factors |
| **4** | **Upstream transportation** | Transport of purchased goods to your facility | Logistics data, tkm-based emission factors |
| **5** | **Waste generated in operations** | Disposal/treatment of your waste | Waste volume × treatment emission factors |
| **6** | **Business travel** | Employee flights, hotels, rental cars | Travel records, DEFRA/EPA factors |
| **7** | **Employee commuting** | Daily commute of employees | Survey + distance × mode factors |
| **8** | **Upstream leased assets** | Emissions from leased assets (not in Scope 1/2) | Energy use of leased facilities |

### Downstream (Categories 9–15)

| Cat | Name | Description | Typical Data Sources |
|-----|------|-------------|---------------------|
| **9** | **Downstream transportation** | Transport of sold products to customers | Logistics data, assumptions on distribution |
| **10** | **Processing of sold products** | Emissions from further processing by customers | Customer process data, industry averages |
| **11** | **Use of sold products** | Emissions during product use phase | Energy consumption during use, product lifetime |
| **12** | **End-of-life treatment** | Disposal of sold products | Waste scenarios, recycling rates |
| **13** | **Downstream leased assets** | Emissions from assets you lease to others | Energy use data from lessees |
| **14** | **Franchises** | Emissions from franchise operations | Franchise energy/operational data |
| **15** | **Investments** | Emissions from financial investments | Investee company emissions, PCAF methodology |

## Materiality Screening

Not all 15 categories are relevant for every company. Screen by:

### Relevance Criteria

| Criterion | Question |
|-----------|----------|
| **Size** | Is this category likely > 5% of total Scope 3? |
| **Influence** | Can you reduce these emissions? |
| **Risk** | Are there regulatory or reputational risks? |
| **Stakeholder** | Do stakeholders expect reporting on this? |
| **Data availability** | Can you reasonably obtain data? |

### Industry Shortcuts

| Industry | Usually material categories | Often immaterial |
|----------|---------------------------|-----------------|
| **Manufacturing** | 1, 2, 4, 5, 11, 12 | 6, 7, 8, 14, 15 |
| **Retail/Consumer** | 1, 4, 9, 11, 12 | 2, 8, 13, 14 |
| **Services/IT** | 1, 2, 6, 7 | 4, 5, 10, 11, 12 |
| **Automotive** | 1, 2, 4, 11 (use phase!) | 6, 7, 14, 15 |
| **Construction** | 1, 2, 4, 5, 12 | 6, 7, 14, 15 |
| **Chemical** | 1, 3, 4, 5, 10 | 6, 7, 14, 15 |

## Calculation Methods

Three approaches, in order of accuracy:

### 1. Supplier-Specific Method (Most Accurate)

```
Emissions = Σ (quantity of product × supplier-specific emission factor)
```
- Use actual LCA data from suppliers
- Best for Category 1, 4
- Requires supplier engagement

### 2. Average-Data Method

```
Emissions = Σ (quantity of product × industry-average emission factor)
```
- Use LCA database emission factors (HiQLCD, ecoinvent)
- Good balance of accuracy and effort
- Most common for initial Scope 3 inventory

### 3. Spend-Based Method (Least Accurate)

```
Emissions = Σ (spend on product/service × EEIO emission factor)
```
- Use environmentally-extended input-output factors ($/€ → kgCO2e)
- Quick screening, low accuracy
- Good for materiality assessment, not for detailed reporting

## Data Collection Workflow

### Step 1: Identify Activities

List all purchased goods, services, logistics, travel, etc.

### Step 2: Categorize

Assign each activity to one of the 15 categories. Use this decision tree:

```
Is it a direct emission from your operations?
  → YES: Scope 1

Is it from purchased electricity/heat/steam?
  → YES: Scope 2

Everything else:
  → Is it upstream (before your operations)?
    → YES: Categories 1-8
  → Is it downstream (after your product leaves)?
    → YES: Categories 9-15
```

### Step 3: Select Method per Category

| Category | Recommended Method | Data Needed |
|----------|-------------------|-------------|
| 1 (Purchased goods) | Average-data → Supplier-specific | Material quantities + LCA emission factors |
| 4 (Transport) | Distance-based | tkm + transport mode emission factors |
| 5 (Waste) | Waste-type specific | kg waste × treatment type emission factors |
| 6 (Business travel) | Distance-based | km/flight × DEFRA factors |
| 11 (Use of products) | Product-specific | Energy per use × lifetime × grid factor |

### Step 4: Collect Data

For each category, prepare a data request:

**Category 1 example (purchased goods):**
```
| Material | Annual Quantity | Unit | Supplier | Country of Origin |
|----------|----------------|------|----------|-------------------|
| Steel sheet | 500 | t | Baosteel | China |
| PE granules | 120 | t | Sinopec | China |
| Cardboard | 80 | t | Local | China |
```

Then use `lca-search` to find emission factors for each material.

### Step 5: Calculate and Report

Sum emissions per category, present in standard format:

```
## Scope 3 Inventory (2024)

| Category | Emissions (tCO2e) | % of Total | Method | Data Quality |
|----------|------------------|------------|--------|-------------|
| 1. Purchased goods | 12,500 | 62% | Average-data | Medium |
| 4. Upstream transport | 3,200 | 16% | Distance-based | Medium |
| 11. Use of products | 2,800 | 14% | Product-specific | Low |
| 5. Waste | 800 | 4% | Waste-type | Medium |
| 6. Business travel | 400 | 2% | Distance-based | High |
| Other | 300 | 2% | Spend-based | Low |
| **Total Scope 3** | **20,000** | **100%** | | |
```

## Connecting to LCA Data Search

When user needs emission factors for Scope 3:

1. **Category 1**: Search by material name → `lca-search` with specific material + geography
2. **Category 3**: Search for well-to-tank fuel factors → `search well-to-tank natural gas`
3. **Category 4**: Search for transport factors → `search road freight transport tkm`
4. **Category 5**: Search for waste treatment → `search municipal waste incineration`
5. **Category 11**: Search for energy use → `search electricity grid mix` for user's market

## Key Standards

| Standard | Scope | Use Case |
|----------|-------|----------|
| **GHG Protocol Corporate Standard** | Scope 1, 2, 3 framework | Corporate carbon footprint |
| **GHG Protocol Scope 3 Standard** | Detailed Scope 3 guidance | 15 categories, calculation methods |
| **ISO 14064-1** | Organizational GHG inventory | International standard |
| **ISO 14067** | Product carbon footprint | Product-level, cradle-to-gate/grave |
| **SBTi** | Science-based targets | Target setting for Scope 3 reduction |
| **CDP** | Disclosure framework | Reporting Scope 3 to investors |
| **PCAF** | Financial sector | Category 15 (investments) |

## Important Notes

- Scope 3 is inherently uncertain — aim for reasonable estimates, not perfect numbers
- Start with materiality screening, focus effort on the biggest categories
- Spend-based method is acceptable for screening but not for detailed reporting
- Always document assumptions, data sources, and exclusions
- Scope 3 inventory should improve over time — first year is the baseline
- For product carbon footprint (ISO 14067), the approach is different from corporate Scope 3
