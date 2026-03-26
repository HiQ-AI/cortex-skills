<p align="center">
  <img src="https://raw.githubusercontent.com/HiQ-AI/cortex-desktop/main/icon.png" width="60" alt="Cortex Skills" />
</p>

<h1 align="center">Cortex Skills Marketplace</h1>

<p align="center">
  Skills for <a href="https://github.com/HiQ-AI/cortex-desktop">HiQ Cortex Desktop</a> — teach your AI new tricks.
</p>

---

## What are Skills?

Skills are instruction files (`.md`) that give Cortex's AI specialized knowledge for specific tasks. When a skill is installed, the AI automatically loads it when the task matches — no manual activation needed.

A skill is just a markdown file with a YAML header. No code, no API, no server. The AI reads the instructions and follows them.

## Available Skills

### 🏢 Office & Documents
| Skill | What it does |
|---|---|
| **xlsx** | Read, write, edit Excel/CSV — formulas, charts, data cleaning |
| **pdf** | Read, merge, split, OCR, watermark, encrypt/decrypt PDFs |
| **docx** | Create and edit Word documents — TOC, headers, formatting |
| **pptx** | Build and edit PowerPoint presentations |

### 🔬 LCA Professional
| Skill | What it does |
|---|---|
| **lca-format-validator** | Validate and convert LCA data packages (ILCD XML, JSON-LD) |
| **bom-analysis** | Analyze BOM lists — dedup, classify, unit normalization, LCA readiness |
| **data-quality-assessment** | Data quality scoring — Pedigree Matrix, PEF DQR, ILCD DQI |
| **scope3-guidance** | GHG Protocol Scope 3 — 15 categories, boundaries, calculation methods |
| **cbam-compliance** | EU CBAM carbon border tax — scope, calculation, reporting |
| **openlca-bridge** | Connect to local openLCA 2.x — import, model, run LCIA calculations |

### 🎨 Creative & Development
| Skill | What it does |
|---|---|
| **frontend-design** | Generate production-grade web UI — components, pages, dashboards |
| **algorithmic-art** | Create generative art with p5.js — particles, flow fields, fractals |
| **canvas-design** | Design posters, infographics, certificates as PNG/PDF |
| **web-artifacts-builder** | Build multi-component React web applications |
| **theme-factory** | Apply themes to slides, documents, reports, HTML |
| **doc-coauthoring** | Structured document collaboration — outline, iterate, review |

### 📦 Meta
| Skill | What it does |
|---|---|
| **product-self-knowledge** | Cortex product capabilities reference |

## Install Skills

In Cortex Desktop:

1. Open **Skills Center** (sidebar)
2. Browse available skills
3. Click **Install** — done

Skills marked `auto_install` are pre-installed with the app.

## Create Your Own Skill

A skill is a folder with one required file:

```
skills/my-skill/
├── SKILL.md          # Required — instructions + YAML frontmatter
├── references/       # Optional — reference docs the AI can load
├── scripts/          # Optional — scripts the AI can execute
└── LICENSE.txt       # Optional — license terms
```

### SKILL.md format

```markdown
---
name: my-skill
description: "When to trigger this skill. Be specific — the AI uses this
  to decide whether to load the skill. Include trigger words, file types,
  and task patterns. Also say what NOT to trigger on."
---

# Skill Title

Your instructions here. Write them like you're briefing a smart colleague:
- What to do
- How to do it well
- Common pitfalls to avoid
- Output format and quality standards
```

### Tips for good skills

- **Description is everything** — the AI decides whether to load your skill based on the `description` field. Be specific about trigger conditions.
- **Write for an expert** — the AI is smart. Don't over-explain basics. Focus on domain-specific rules, edge cases, and quality standards.
- **Include examples** — show what good output looks like.
- **Say what NOT to do** — "Do NOT trigger when..." prevents false activations.
- **Use references/** for large docs — put detailed specs, standards, or templates in `references/` and tell the AI to load them with `get_skill_reference`.
- **Use scripts/** for automation — put reusable scripts in `scripts/` and tell the AI to run them with `get_skill_script`.

### Test your skill

1. Copy your skill folder to `~/.claude/skills/` (or Cortex's skills directory)
2. Start a Cowork session
3. Give it a task that should trigger the skill
4. Check if the AI loaded it (`get_skill_instructions` should appear in tool calls)

## Submit to Marketplace

1. Fork this repo
2. Create `skills/{your-skill-name}/SKILL.md`
3. Add your skill to `marketplace.json`:
   ```json
   {
     "id": "your-skill-name",
     "name": "Display Name",
     "description": "Chinese description for the marketplace UI",
     "version": "1.0.0",
     "author": "Your Name",
     "tags": ["category"],
     "path": "skills/your-skill-name"
   }
   ```
4. Submit a PR — we'll review and merge

### Review criteria

- **Useful** — solves a real problem for LCA professionals or general productivity
- **Well-written** — clear instructions, specific triggers, good examples
- **No conflicts** — doesn't overlap with existing skills
- **Tested** — you've verified it works in Cortex Desktop

### LCA skills especially welcome

We're building the most comprehensive AI-powered LCA toolkit. These scenarios from our [Ideas list](https://github.com/HiQ-AI/cortex-desktop/issues/12) need skills:

- Flow balance validation (mass/energy conservation)
- GWP reasonableness checking
- Dataset metadata auto-completion
- PCR database lookup
- EPD drafting assistance
- ISO 14067 report templates
- Sensitivity analysis
- Industry benchmark databases

If you build one, we'll credit you in the release notes.

---

## How It Works (Technical)

Cortex Desktop fetches `marketplace.json` from this repo at startup. The Skills Center UI displays available skills. When a user installs a skill, the app downloads the skill folder and places it in the local skills directory.

At runtime, installed skills are registered with the AI agent. The AI automatically calls `get_skill_instructions(skill_name)` when it detects a matching task based on the skill's `description` field.

---

<p align="center">
  <sub>Part of <a href="https://github.com/HiQ-AI/cortex-desktop">HiQ Cortex</a> · Built by <a href="https://www.hiqlcd.com">HiQ AI</a></sub>
</p>
