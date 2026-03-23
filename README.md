# HiQ Cortex Skills Marketplace

Downloadable skills for [HiQ Cortex Desktop](https://github.com/HiQ-AI/cortex-desktop).

## Skills

| Skill | Description |
|-------|-------------|
| xlsx | Excel/CSV spreadsheet operations |
| pdf | PDF reading, merging, splitting, OCR |
| docx | Word document creation and editing |
| pptx | PowerPoint presentation building |
| frontend-design | High-quality frontend UI generation |
| product-self-knowledge | Cortex product capabilities reference |

## How it works

Cortex Desktop fetches `marketplace.json` from this repo to display available skills. Users can install/uninstall skills from the Skills Center in the app.

## Adding a new skill

1. Create a directory under `skills/{skill-name}/`
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`)
3. Add the skill to `marketplace.json`
4. Submit a PR
