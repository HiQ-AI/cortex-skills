---
name: lca-format-validator
description: "Parses, validates, and converts LCA data packages (ILCD, openLCA JSON-LD, TIDAS). Triggers on uploaded ILCD/JSON-LD/TIDAS files, "format check", "数据包校验", "格式验证", "ILCD解析", or requests to inspect package contents. Does NOT search LCA data — use lca-search for that."
---

# LCA Format Validator

Parse, validate, and convert LCA data packages. Supports ILCD XML, openLCA JSON-LD, and TIDAS JSON formats.

## Quick Reference

The toolkit script is at: `${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py`

### Commands

```bash
# Parse: extract summary of what's inside a data package
python ${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py parse <path-to-zip-or-dir>

# Validate: check structure, required fields, UUID format, cross-references
python ${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py validate <path-to-zip-or-dir>

# Convert: ILCD XML → JSON (raw xmltodict style)
python ${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py convert <path-to-ilcd.zip> --to json

# Convert: ILCD XML → openLCA JSON-LD zip
python ${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py convert <path-to-ilcd.zip> --to jsonld

# Convert: openLCA JSON-LD → ILCD XML zip
python ${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py convert <path-to-jsonld.zip> --to ilcd
```

### Supported Formats

| Format | Extension | Auto-detected by |
|--------|-----------|-----------------|
| ILCD XML | `.zip` with `ILCD/processes/*.xml` | XML files in ILCD directory structure |
| openLCA JSON-LD | `.zip` with `processes/*.json` | `olca-schema.json` or JSON in category folders |
| TIDAS JSON | directory with `processes/*.json` | JSON files in category subdirectories |

## Workflow

### 1. User uploads a data package

When the user provides a file path or uploads an ILCD/JSON-LD/TIDAS zip:

1. **First**: Run `parse` to show what's inside
2. **Then**: Ask if they want validation
3. **If validation requested**: Run `validate` and explain the report
4. **If they want to find alternatives**: Use the parsed process names to search via `mcp__cortex__search_lca_datasets`

### 2. User asks "is this file valid?"

1. Run `validate` on the file
2. Present the Markdown report (the script outputs Markdown directly)
3. Explain each issue in plain language:
   - 🔴 Errors = must fix (missing UUID, invalid XML, no exchanges)
   - 🟡 Warnings = should fix (missing optional fields, no flow type)
4. A JSON report is also saved as `*_validation_report.json`

### 3. User wants format conversion

1. **ILCD XML → JSON**: `convert --to json` (raw xmltodict style)
2. **ILCD XML → JSON-LD**: `convert --to jsonld` — generates openLCA-compatible JSON-LD zip
3. **JSON-LD → ILCD XML**: `convert --to ilcd` — generates complete ILCD zip package

All 7 dataset types supported in both directions: Process, Flow, FlowProperty, UnitGroup, Source, Contact/Actor, ImpactCategory/LCIA Method.

## Validation Rules

The validator checks:

**For all formats:**
- Valid UUID format (8-4-4-4-12 hex pattern)
- Required fields present (name, UUID/ID)
- File parseable (valid XML/JSON)

**For ILCD XML:**
- UUID exists in each dataset
- Process has baseName
- Process has exchanges with direction (Input/Output)
- Flow has baseName and typeOfDataSet

**For openLCA JSON-LD:**
- @id and @type fields present
- name field present
- Process has exchanges with quantitative reference
- Exchange has flow reference
- Flow has flowType

**For TIDAS JSON:**
- Root key matches category (processDataSet, flowDataSet, etc.)
- Filename UUID matches content UUID
- Language constraints: zh text must contain Chinese, en text must not contain Chinese

## Requirements

- **Python 3.9+** — macOS/Linux 自带，Windows 需安装
- **jsonschema + referencing** — 首次运行时自动 `pip install`（用于完整的 JSON Schema Draft-7 验证）

首次使用时脚本会自动安装依赖。如果安装失败，会降级为结构校验模式（仅检查关键字段，不做完整 schema 验证）。

### 首次使用

```bash
# 脚本会自动安装依赖，无需手动操作
python ${CLAUDE_SKILL_DIR}/scripts/lca_toolkit.py validate <file>
# 输出: [LCA Toolkit] Installing jsonschema...
# 后续运行不再安装
```

## Understanding ILCD Structure

An ILCD package contains 7 dataset types:

```
ILCD/
├── processes/       ← Unit/system processes (the main datasets)
│   └── {uuid}.xml      inputs & outputs (exchanges), geography, time
├── flows/           ← Material/energy/emission flows
│   └── {uuid}.xml      name, CAS number, flow type, properties
├── flowproperties/  ← Quantity types (mass, energy, volume)
├── unitgroups/      ← Unit definitions (kg, MJ, m³)
├── sources/         ← Literature references
├── contacts/        ← Organizations/people
└── lciamethods/     ← Impact assessment methods (GWP factors)
```

Processes reference Flows by UUID. Flows reference FlowProperties. FlowProperties reference UnitGroups. This forms a reference chain that must be valid for the package to be complete.

## Understanding openLCA JSON-LD Structure

```
├── olca-schema.json      ← Version metadata {"version": 2}
├── processes/             ← Process datasets
│   └── {uuid}.json           exchanges[], location, processType
├── flows/                 ← Flow datasets
│   └── {uuid}.json           flowType, flowProperties[]
├── flow_properties/       ← FlowProperty datasets
├── unit_groups/           ← UnitGroup datasets
├── lcia_categories/       ← Impact categories
├── lcia_methods/          ← Impact methods
├── actors/                ← Contact/organization
├── sources/               ← Literature references
└── locations/             ← Geographic locations
```

Key differences from ILCD: uses `@id`/`@type` (JSON-LD style), `isInput` boolean instead of `exchangeDirection`, `isQuantitativeReference` flag on exchanges.
