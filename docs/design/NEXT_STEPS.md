# Next Steps & Carry-Forwards

State as of 3 Aug 2026, commit `1dd6e69`. Phase 0 + Phase 1 (vertical slice) are code-complete: **backend 52 tests, ai_agents 15 tests, frontend build clean — all zero warnings.** Every task passed a scoped review, and a final whole-branch review plus its fix wave are merged.

**Not yet done: live verification.** See `slice-verification.md` — the automated half is recorded honestly; the live half has never run. The `v0.1-slice` tag is deliberately NOT created until it does.

---

## 1. Your manual steps (in this order)

**A. API keys → `backend/.env`**
```bash
cp backend/.env.example backend/.env
```
Fill in three values:
- `GEMINI_API_KEY` — https://aistudio.google.com/apikey (free, no card, ~1500 req/day)
- `GROQ_API_KEY` — https://console.groq.com/keys (free, no card) — the fallback
- `DATABASE_URL` — Supabase → new project (region **ap-south-1**) → Settings → Database → Connection string → **Session pooler**.
  ⚠️ Supabase gives you `postgresql://…`; this project needs **`postgresql+psycopg://…`**. Add `+psycopg` and replace `[YOUR-PASSWORD]`.

**B. Prove both providers respond**
```bash
cd backend && .venv/Scripts/python ../scripts/smoke_llm.py
```
Expect two `OK` lines. If Gemini 429s, wait a minute (free-tier RPM) and retry.

**C. Create the database tables**
```bash
cd backend && .venv/Scripts/python ../scripts/create_tables.py
```
It now prints the resolved DB target first — **check it says your Supabase host, not a local sqlite file** before letting it run.

**D. Get data for at least one category**
```bash
ai_agents/.venv/Scripts/python scripts/fetch_amazon.py grocery
```
(~100K reviews. The 4.35 GB Yelp download for `food_restaurants` can wait — one category is enough to demo.)

**E. Precompute the sentiment**
```bash
cd ai_agents && .venv/Scripts/python -m agent3_customer.precompute grocery
```
Also prints its DB target first. Takes a few minutes (VADER over 100K reviews).

**F. Run it**
```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
cd frontend && npm run dev     # separate terminal → http://localhost:5173
```

**G. Then fill in the live rows** of `docs/design/slice-verification.md` with real observations, and only then create the `v0.1-slice` tag.

---

## 2. Verify during your live run

These could not be tested offline and are worth watching:

- **`timeout=30` is accepted** by the installed `langchain-google-genai` / `langchain-groq` versions. No test constructs the real client classes, so this is unproven.
- **Chunk content shape.** `gemini-2.5-flash` is a thinking model; `_as_text()` in `llm.py` normalizes list-shaped content, but only fakes have exercised it. If you ever see `[object Object]` streaming, that's the path.
- **Keyword quality on real data.** `top_keywords_contrastive` subtracts the praise/complaint overlap. Check the real output actually reads as distinct insight rather than generic nouns.
- **Backend logs** now name the provider on every attempt and warn on fallback — that's how you prove the Groq fallback fired.

---

## 3. Deferred items for Phase 2

Reviewed, judged non-blocking, deliberately carried:

| Item | Where | Do it when |
|---|---|---|
| `PRAGMA foreign_keys=ON` in the SQLite test fixture | `backend/tests/conftest.py` | Phase 4 auth, when `users → strategies` starts mattering |
| `Query(max_length=500)` on the `idea` param | `backend/app/routers/analyze.py` | Phase 4 security pass |
| `get_settings` lru_cache not cleared after tests | `backend/tests/test_config.py` | When more tests start reading settings |
| Payload keys indexed directly → `KeyError` risk | `backend/app/services/customer_agent.py` | **Tripwire: the day a second agent writes to `category_insights`** |
| `<textarea>` has no `<label>` | `frontend/src/pages/SlicePage.jsx` | Phase 4 UI |
| Unused Vite scaffold leftovers | `frontend/src/assets/`, `App.css` | Any cleanup pass |
| Head-of-stream sampling, not random | `scripts/fetch_amazon.py`, `sample_yelp.py` | Before the report claims "random sample" — see §4 |
| `"Food"` substring pulls Yelp grocery/bakery into `food_restaurants` | `ai_agents/scripts_lib/sampling.py` | If the two demo categories need clean separation |

**Structural work Phase 2 needs early:** extract the 8 category slugs to one shared constant (six more agents will use them), write `docs/design/agent-contract.md` while there's exactly one implementation to describe, and rework the `HTTPException`-based error path into the roadmap's `{status: "failed", retryable: true}` contract for the parallel-agent UI.

---

## 4. Two academic notes

- **EDA notebooks.** The roadmap asks for "6 EDA notebooks with a couple of plots" as a Review-1 deliverable. The plan substituted `scripts/eda_report.py`, which emits a table with **no plots**, and `ai_agents/agent3_customer/notebooks/` is empty. Decide deliberately: accept the substitution, or schedule the notebooks before Review 1.
- **Sampling wording.** The datasets are head-of-stream subsets, not random samples. *"How did you sample, and did you check for bias?"* is a standard viva question. Either implement reservoir sampling or state plainly in `docs/eda/DATASETS.md` that it's a head-of-stream subset — the honest label costs nothing and is defensible.
