# AI Business Strategy Advisor

Solo college mini project (2026). Type a business idea → 7 AI agents analyze
real datasets → an LLM streams back a data-grounded strategy report.

- Planning docs: `01_DEEP_RESEARCH_FEASIBILITY.md`, `02_STEP_BY_STEP_ROADMAP.md`
- Implementation plans: `docs/superpowers/plans/`
- Architecture rule: **precompute heavy (ai_agents/), serve light (backend/)**

## Layout
- `backend/` — FastAPI API (light deps only)
- `frontend/` — React + Vite + Tailwind
- `ai_agents/` — offline ML: dataset sampling + per-agent precompute
- `scripts/` — data acquisition
- `data/` — sampled datasets (gitignored; recreate via scripts)
