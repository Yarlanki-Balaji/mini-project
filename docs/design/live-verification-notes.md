# Live Verification Notes — Gemini Model Gating (2026-08-03)

## What failed

The first live verification run made a real Gemini API call with a freshly-created
key, using the pinned model ID `gemini-2.5-flash` (as set in `backend/app/services/llm.py`
and `scripts/smoke_llm.py`). The call failed with:

```
404 NOT_FOUND: This model models/gemini-2.5-flash is no longer available to new users.
Please update your code to use a newer model for the latest features and improvements.
```

The model still appears in Google's model-list endpoint, but new API keys are gated
off from calling it. Existing keys created before the gating change may still work,
which is why this was not caught by pre-live suites — it only surfaces with a
genuinely fresh key against the live endpoint.

## What was verified about model availability

Checked directly against the live model-list endpoint and by streaming real
completions with the project's Gemini key:

| Model | Result |
|---|---|
| `gemini-2.5-flash` | Listed by the API but gated off for new keys. 404 on invoke. Dead for this project. |
| `gemini-flash-latest` | Works. Streams correctly. Rolling alias that always points at the current flash model. |
| `gemini-3.6-flash` | Works (pinned version). |
| `gemini-2.0-flash` | Quota-exhausted on the free tier. |

## Decision: use `gemini-flash-latest`

Chosen over pinning to `gemini-3.6-flash`. Rationale: this project is a student
mini-project that must still work at a graded demo months from now. We just watched
a *pinned* model ID get gated off with no warning; a rolling alias is the failure
mode we can actually defend against. The trade-off — behaviour may drift as Google
advances the alias — is acceptable here because the prompt is simple synthesis, and
the Groq fallback (`llama-3.3-70b-versatile`, unchanged) covers a bad day.

Applied in:
- `backend/app/services/llm.py` — `gemini_llm()` factory, plus a 2-line code comment
  recording this rationale.
- `scripts/smoke_llm.py` — same model ID.
- `docs/design/NEXT_STEPS.md` — prose reference updated to match.

Historical planning docs (`docs/superpowers/plans/`, `01_DEEP_RESEARCH_FEASIBILITY.md`,
`02_STEP_BY_STEP_ROADMAP.md`) were deliberately left unchanged — they are records of
what was planned, not live config.

## Chunk content shape — confirmed, `_as_text()` handles it correctly

Confirmed against the live API: Gemini returns `chunk.content` as a **list of
dicts**, e.g.:

```python
[{'type': 'text', 'text': 'It saves time...', 'index': 0}]
```

not a plain string. `_as_text()` in `backend/app/services/llm.py` already normalizes
this correctly — it detects the list case and joins each part's `text` field into
plain text. This code path was read and confirmed intact after the model-ID change;
it was not modified. Without this normalizer, the frontend would render raw Python
dict reprs (`[object Object]`-style output) into the streamed strategy text instead
of readable words.

## Smoke-test output (real API calls, no keys included)

Command: `.venv/Scripts/python ../scripts/smoke_llm.py` (run from `backend/`)

```
GEMINI: [{'type': 'text', 'text': 'OK', 'extras': {'signature': 'EoYCCoMCARFNMg8...'}}]
GROQ: OK
```

Both providers responded successfully with the new model ID. The Gemini line shows
the raw list-of-dicts shape returned by `.invoke(...).content` directly (the smoke
script prints the raw content, unlike `stream_strategy()` in `llm.py`, which routes
through `_as_text()` to flatten it before it reaches the UI).

## Suite results after the fix

- Backend: `.venv/Scripts/python -m pytest -v` — 52 passed, zero warnings.
- `git status` confirmed `backend/.env` was not staged or tracked at any point.
