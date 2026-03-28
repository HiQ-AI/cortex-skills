---
name: openlca-bridge
description: "Connects to openLCA for LCA calculations, product system building, and LCIA (ReCiPe, CML, EF 3.0). Triggers on "openLCA", "run LCIA", "build product system", "impact assessment", "导入openLCA", "跑计算", "影响评价". Does NOT search data — use lca-search for that."
---

# openLCA Bridge

Connect Cortex to openLCA 2.x via IPC. Search data with Cortex, calculate with openLCA — complete LCA workflow without switching tools.

## Prerequisites

Before using this skill, the user must:
1. Have **openLCA 2.x** installed and running
2. Open a database in openLCA (ecoinvent, ELCD, or other)
3. Start the IPC server: **Tools > Developer Tools > IPC Server** (default port 8080)

If the user hasn't done this, guide them through setup before proceeding.

## Quick Reference

Bridge script: `${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py`

```bash
# Test connection
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py ping

# Explore database
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py databases
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py processes --search "steel"
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py flows --search "CO2"
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py methods

# Import data from Cortex (JSON-LD zip from lca-format-validator)
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py import-jsonld <path-to-jsonld.zip>

# Build product system
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py create-system "Steel production"

# Run LCIA calculation
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py calculate "Steel production" --method "ReCiPe 2016 Midpoint (H)" --amount 1000

# Query results
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> impacts
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> contributions "climate change"
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> flows
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> dispose
```

## Dependencies

- **Python 3.11+**
- **olca-ipc** — auto-installed on first run (`pip install olca-ipc`)
- **openLCA 2.x** — user must have it running with IPC server enabled

## Complete Workflow

### Step 1: Verify Connection

Always start by testing the connection:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py ping
```

If connection fails, guide the user:
1. "Is openLCA running?"
2. "Did you open a database?"
3. "Go to Tools > Developer Tools > IPC Server, click Start"
4. "The default port is 8080. If you changed it, tell me."

### Step 2: Explore Available Data

Before doing anything, check what's in the user's openLCA database:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py databases
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py methods
```

This tells you how many processes/flows are loaded and which LCIA methods are available.

### Step 3: Search and Match Background Data (Cortex + openLCA)

Two approaches:

**Approach A: Data already in openLCA**
User's database already has the processes they need. Search within openLCA:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py processes --search "carbon steel"
```

**Approach B: Data from Cortex search → Import to openLCA**
1. Use `lca-search` (MCP tool) to find datasets in Cortex's 12 databases
2. Use `lca-format-validator` to export as JSON-LD zip
3. Import into openLCA:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py import-jsonld matched_data.zip
```

### Step 4: Create Product System (HITL)

Ask the user which process is the reference process for their product:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py create-system "Steel production, converter"
```

The product system auto-links all upstream processes. Use `--prefer-unit` to prefer unit processes over system processes.

### Step 5: Choose LCIA Method (HITL)

List available methods and let the user choose:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py methods
```

Common choices:
| Method | Use Case |
|--------|----------|
| **IPCC 2021 GWP 100a** | Carbon footprint only (GWP) |
| **ReCiPe 2016 Midpoint (H)** | Full midpoint assessment (18 categories) |
| **ReCiPe 2016 Endpoint (H)** | Aggregated damage assessment |
| **EF 3.0 / 3.1** | EU PEF compliance |
| **CML-IA baseline** | Classic midpoint method |
| **TRACI 2.1** | US EPA standard |

Use AskUserQuestion to let the user select.

### Step 6: Run Calculation

```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py calculate "Steel production" \
  --method "IPCC 2021 GWP 100a" --amount 1000
```

The result includes all impact category values. Save the `result_id` for follow-up queries.

### Step 7: Interpret Results

Present results clearly:

**Total impacts:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> impacts
```

**Which processes contribute most (hotspot analysis):**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> contributions "climate change"
```

**Inventory flows (for verification):**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> flows
```

Present results as a table with units. Explain what each impact category means in plain language.

### Step 8: Comparison (Optional)

If the user wants to compare alternatives:
1. Run calculation for each alternative
2. Present results side by side
3. Highlight differences and trade-offs

### Step 9: Cleanup

Release server resources when done:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/olca_bridge.py result <id> dispose
```

## Integration with Other Skills

| Step | Skill Used | What It Does |
|------|-----------|-------------|
| Search background data | `lca-search` | Find datasets in 12 databases |
| Validate data package | `lca-format-validator` | Check ILCD/JSON-LD format |
| Convert to JSON-LD | `lca-format-validator` | ILCD → JSON-LD for import |
| Assess data quality | `data-quality-assessment` | Score representativeness |
| Import into openLCA | **this skill** | `import-jsonld` command |
| Build product system | **this skill** | `create-system` command |
| Run calculation | **this skill** | `calculate` command |
| Interpret results | **this skill** | `result impacts/contributions` |

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Connection refused | openLCA IPC not started | Guide user to start IPC server |
| Process not found | Name mismatch | Use `processes --search` to find exact name |
| Method not found | Method not installed | Use `methods` to list available, or install method pack in openLCA |
| Import failed | Incompatible format | Check JSON-LD version, ensure openLCA 2.x |
| Calculation error | Incomplete product system | Check for missing providers, broken links |

## Important Notes

- All calculations run in openLCA on the user's machine — no data leaves their computer
- The IPC server must be running throughout the session
- Large calculations (many processes) may take 10-60 seconds
- Results are held in memory — always `dispose` when done
- openLCA IPC port defaults to 8080; if user changed it, use `--port` flag
- If Python < 3.11, olca-ipc won't install — user needs to upgrade Python
