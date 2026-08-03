# Vertical Slice Verification — Automated Checks Only (live verification pending)

This document currently records only the automated test/build evidence. The
live, browser-and-API half of verification (real Gemini call, Groq fallback,
3-scenario browser check) has **not** been run — see "Live verification —
NOT YET RUN" below.

**Date:** 2026-08-03
**Commit:** 194aa04 (the app commit the suites below were run against — this
is the parent of the commit that adds this document, so the SHA recorded
here intentionally predates the commit that introduces this file)

Definition of done (roadmap Phase 1): idea typed in browser → matched category
shown while typing → real complaint/praise data → strategy streamed word-by-word.

## Automated verification (run 2026-08-03)

| Check | Result |
| --- | --- |
| backend pytest suite | verbatim summary line: `============================= 49 passed in 1.16s ==============================` — no warnings summary was emitted, so no warnings were reported |
| ai_agents pytest suite | verbatim summary line: `============================= 13 passed in 45.34s ==============================` — no warnings summary was emitted, so no warnings were reported |
| frontend `npm run build` | exit 0, built in 292ms — dist/index.html 0.45 kB (gzip 0.29 kB), dist/assets/index-COQI-moC.css 7.92 kB (gzip 2.31 kB), dist/assets/index-DXapQXfg.js 239.84 kB (gzip 78.41 kB) |

Commands actually run:

```bash
cd "C:/Users/Balaji/Desktop/mini project/backend" && .venv/Scripts/python -m pytest -v
cd "C:/Users/Balaji/Desktop/mini project/ai_agents" && .venv/Scripts/python -m pytest tests -v
cd "C:/Users/Balaji/Desktop/mini project/frontend" && npm run build
```

Note: the ai_agents invocation includes an explicit `tests` path argument,
which differs textually from the Task 13 brief's `pytest -v` (no path). This
is equivalent in effect because `ai_agents/pytest.ini` already sets
`testpaths = tests`, so both forms collect the same 13 tests — confirmed by
the "collected 13 items" line in the captured output. The command was not
silently changed to match the brief; this is the command actually run.

All three exited green with no retries needed. Verified immediately beforehand
that none of the live-verification prerequisites exist on this machine:
`backend/.env` is absent, `~/.kaggle/kaggle.json` is absent, and both
`data/processed/` and `data/raw/` contain only `.gitkeep` (no sampled
datasets, no precomputed `CategoryInsight` rows).

## Live verification — NOT YET RUN

These require the human partner's API keys and sampled datasets, neither of
which exist yet. They are deliberately unrecorded rather than assumed.

| Check | Status | Blocked by |
| --- | --- | --- |
| Food idea end-to-end via Gemini | NOT RUN | no `backend/.env` (GEMINI_API_KEY) |
| Groq fallback with Gemini key broken | NOT RUN | no `backend/.env` (GROQ_API_KEY) |
| Out-of-scope idea friendly path (browser) | NOT RUN | backend requires precomputed data |
| Live category preview while typing | NOT RUN | backend not started |
| Time to first streamed token | NOT RUN | no live LLM call possible |
| Screenshots (2-3, per brief template) | NOT RUN | requires a running backend and a live browser session; none exist yet |

## What the automated suites do and do not prove

**What passes and why it's meaningful.** All 62 automated tests (49 backend +
13 ai_agents) pass, and the frontend production bundle builds cleanly. This
proves the code that exists is internally consistent: request/response
contracts hold their shape, category-matching keyword logic is correct
(including word-boundary edge cases like `spa` not matching `space tourism`),
the sentiment-aggregation math (percentages, keyword bucketing) is exact, the
SQLAlchemy schema round-trips nested JSON and enforces its uniqueness
constraint, the SSE stream frames JSON correctly and always terminates with a
`done` frame, and the LLM-fallback control flow (primary → secondary on
failure, error frame when both fail) executes the code paths it's supposed
to. The frontend TypeScript/JSX compiles and Vite can produce a deployable
bundle.

**What it cannot prove, given how the suite is built.** Every test that
touches an LLM (`tests/test_llm.py`, `tests/test_stream.py` in `backend/`)
calls a **fake/stub provider object**, not Gemini or Groq — no real network
request, no real API key, no real token stream, no real model output was
ever exercised. `test_stream_falls_back_when_primary_raises` proves the
Python `try/except` branch runs when the primary callable raises, not that a
genuine Gemini outage triggers a genuine Groq completion; the "fallback" in
this test suite is a mock function raising `Exception("boom")`, not an
invalid `GEMINI_API_KEY` against Google's real endpoint. Similarly, every
database interaction in both suites (`test_schema.py`, `test_customer_agent.py`,
sampling/sentiment tests) runs against an **in-memory or temp-file SQLite
database seeded with a handful of synthetic fixture rows** — not the
Supabase Postgres `DATABASE_URL` the app will actually use in production, and
not the real Yelp/Amazon-review-derived `CategoryInsight` rows that
`ai_agents` is meant to compute from Kaggle data. No test in either suite
reads a byte of the real sampled dataset, because no such dataset exists yet
on this machine (`data/processed/` and `data/raw/` are empty except for
`.gitkeep`).

Concretely: **62 tests passing is evidence the code is logically correct in
isolation.** It is not evidence that a person can open the browser, type a
food-business idea, watch a category match appear, see real Yelp sentiment
render, and watch a real Gemini (or Groq-fallback) strategy stream in
word-by-word. That end-to-end claim — the actual Phase 1 definition of done —
remains unverified until the live rows above are run with real credentials
and real data.

## To complete verification

1. Obtain a Google Gemini API key and a Groq API key; create
   `backend/.env` with `GEMINI_API_KEY=...`, `GROQ_API_KEY=...`, and the
   Supabase `DATABASE_URL=...`.
2. Set up `~/.kaggle/kaggle.json` with valid Kaggle API credentials so the
   `ai_agents` sampling scripts can download the Yelp/Amazon-review source
   data.
3. Run the `ai_agents` sampling and sentiment-aggregation pipeline to
   populate `data/raw/` and `data/processed/`, and to write real
   `CategoryInsight` rows into the database the backend reads from.
4. Start the backend (`uvicorn` / project's run command) and the frontend
   dev server.
5. In the browser, run the 3-scenario check from Task 12 Step 4: a
   food-business idea (in-scope), an idea that maps to a different supported
   category, and an out-of-scope idea. Confirm the category preview updates
   while typing, real sentiment data renders, and the strategy streams
   word-by-word with a real Gemini call (check backend logs to confirm no
   fallback fired). Record the observed seconds-to-first-token.
6. Temporarily set `GEMINI_API_KEY=broken` in `backend/.env`, restart the
   backend, repeat one scenario, and confirm in backend logs that the
   response still streams via the Groq fallback. Restore the real key
   afterward.
7. Fill in the "Live verification" table above with the real observed
   results (pass/fail, timing, log excerpts) — replacing `NOT RUN` only with
   values actually observed, never a placeholder.
8. Only after all live rows are genuinely green, create the `v0.1-slice` git
   tag (`git tag v0.1-slice`) and push it.
