---
name: product-self-knowledge
description: 'Provides verified facts about HiQ products — Cortex Desktop features, HiQLCD database coverage, HiQ platform capabilities. Triggers when responding about Cortex capabilities, supported databases, data coverage, pricing, company info, "产品功能", "数据库介绍", or comparisons with other LCA tools. Does NOT trigger for general LCA methodology or competitor product details.'
---

# HiQ Product Knowledge

## Core Principles

1. **Accuracy over guessing** — Check this skill when uncertain about product details
2. **Distinguish products** — HiQ Cortex (desktop app), HiQLCD (database platform), HiQ (company)
3. **Right context** — Answer based on the specific product being asked about

---

## HiQ Cortex Desktop

AI-powered LCA data workbench. Available for macOS, Windows, and Linux.

**Download:** https://github.com/HiQ-AI/cortex-desktop/releases

### Two Modes

**Chat** — Cloud-powered LCA Q&A:
- Conversation memory (cloud-synced)
- Expert knowledge base (LCA methodology, standards, best practices)
- Cross-database search, comparison, methodology explanation

**Cowork** — Local-first AI workbench:
- Files stay local — AI reads, writes, edits files on your machine
- Local execution — Python, Shell, data processing runs locally
- Autonomous task planning, sub-task delegation, parallel search
- Skills system — extensible with marketplace + custom skills

### Core Capabilities

- **LCA Data Search** — Searches 12 databases, 1,000,000+ emission factor datasets
- **BOM Matching** — Upload a BOM spreadsheet, auto-match background data for all materials
- **HITL (Human-in-the-Loop)** — Asks clarifying questions when queries are ambiguous
- **File Processing** — Read/write Excel, PDF, Word, PowerPoint natively
- **Professional Commentary** — Provides LCA expert assessment on data quality, regional applicability

### Data Sources (12 databases)

- **HiQLCD** — Chinese LCA database, 15,000+ datasets, 25+ industry sectors
- **Ecoinvent** — Global LCA database, 100+ countries
- **CarbonMinds** — Chemical industry LCA data
- **TianGong (天工)** — Chinese national LCA database
- And 8 more integrated sources

### Skills System

- **Built-in skills:** LCA Search (core), Excel, PDF, Word, PowerPoint, Frontend Design
- **Skill Marketplace:** Cloud-based, one-click install from HiQ-AI/cortex-skills
- **Custom skills:** Import .skill/.zip files with SKILL.md
- Skills extend AI with specialized knowledge and workflows
- Enable/disable per skill, takes effect in new conversations

### Technical

- Built with Electron + Claude Agent SDK
- LLM: Claude Sonnet 4.6 via LiteLLM proxy
- MCP: Deck MCP Server for LCA data search
- Local execution: Bash, Python, file operations

---

## HiQLCD — Chinese Life Cycle Inventory Database

China's leading locally-developed LCA database.

**Website:** https://www.hiqlcd.com

- 📊 15,000+ datasets
- 🏭 25+ Chinese industry sectors: energy, raw materials, processing, transportation, etc.
- 📋 ISO 14040/44, ISO 14067 & ILCD compliant
- 🔗 Compatible with openLCA, SimaPro & more
- 🔄 Regular version updates (current: v1.4.0)

### Coverage

Energy, metals & mining, chemicals, plastics & polymers, building materials, transportation, packaging, electronics, agriculture, textiles, waste treatment, and more.

### Standards Compliance

- ISO 14040/14044 (LCA methodology)
- ISO 14067 (Carbon footprint of products)
- ILCD (International Life Cycle Data System)
- EU CBAM compatible
- Battery passport requirements compatible

---

## HiQ (海科数据) — Company

Shanghai HiQ Smart Data Co., Ltd.

**Websites:**
- China: https://www.hiqlcd.com
- Global: https://hiq.earth

**About:**
LCA data technology company founded by LCA experts and engineers. Provides professional LCA data resources, intelligent tools, and data services for corporate sustainability, government policy, and academic research.

**Key facts:**
- 100+ enterprise clients (automotive, electronics, packaging, construction, chemicals)
- 18+ strategic partners (Tsinghua University, Tongji University, Fudan University, etc.)
- ecoinvent data partnership
- openLCA ecosystem collaboration

**Contact:**
- Email: info@hiqlcd.com
- Phone: +86-21-61810170
- Location: Shanghai, China

---

## What Cortex Does (and Doesn't Do)

Cortex is **NOT** an LCA modeling tool. It doesn't replace SimaPro, GaBi, or openLCA — it works alongside them.

| Cortex does | LCA tools do |
|---|---|
| Search & match background data | Build product system models |
| Compare data across databases | Calculate impact assessment |
| Explain methodology differences | Generate certified reports |
| Process BOM spreadsheets | Define allocation rules |
| Export matched data for import | Run sensitivity analysis |

---

## Response Guidelines

When answering product questions:
1. Identify which product (Cortex / HiQLCD / HiQ company)
2. Use facts from this skill, not training data
3. If uncertain about current pricing or specific numbers, say "please check the website for the latest information"
4. Include relevant URLs when helpful
