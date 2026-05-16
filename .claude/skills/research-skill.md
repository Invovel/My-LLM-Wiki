# Research Skill v2.1 — Data Collection Only

> Academic paper & GitHub repo data collection.
> **All maintenance (dedup, hotlist, storage) delegated to LLM-Wiki Skill.**

## Commands
| Command | Purpose |
|---------|---------|
| `/research paper <query>` | Search arXiv → download PDF → extract → hand off to LLM-Wiki |
| `/research github <query>` | Search GitHub → get README → hand off to LLM-Wiki |
| `/research config` | View/set download path |
| `/research hotlist` | View LLM-Wiki GitHub trending list |

## Workflow: Paper
1. `search_arxiv.py "query" --max 5`
2. `epoch_manager.py filter "<query>|<ids>|<keywords>"` → LLM-Wiki dedup
3. Download only new PDFs (urllib + User-Agent)
4. Extract text (PyMuPDF → pypdf → arXiv abstract fallback)
5. Package results + `epoch_manager.py register`

## Workflow: GitHub
1. `hotlist_manager.py check "<query>"` → check trending first
2. `gh search repos` or REST API
3. Get README
4. Package → hand off to LLM-Wiki

## LLM-Wiki Handoff Protocol
Research Skill outputs structured JSON. LLM-Wiki handles:
- Formatting & archiving to `wiki/research/`
- Epoch dedup with heat decay (`_epochs.json`)
- GitHub trending hotlist (`_hotlist.json`)
- Cross-referencing with existing Wiki pages

## Config
`~/.hermes/research-config.json`
- `download_path`: PDF download directory
- `wiki_vault_path`: Path to WikiVault
- `search_window_days`: Default 180 days
