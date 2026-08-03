# Step-by-Step Solo Roadmap — AI Business Strategy Advisor

> Companion to `01_DEEP_RESEARCH_FEASIBILITY.md`. This is the **ideation-phase plan** — no code yet.
> Timeline: solo, ~10–15 hrs/week, AI-assisted. Nominal: **11 weeks + ~2 weeks buffer — fits the ~3-month window** (start ≈ mid-Aug 2026 → final demo ≈ mid-Nov 2026).
> If you have more/less time per week, phases stretch or compress — the *order* never changes.
> UX decisions locked 3 Aug 2026 (see **UX Blueprint**). All remaining decisions locked 3 Aug 2026 (see **Decision Log** at the end). Evaluation mode: **local demo** — public deployment is an optional stretch.

---

## The 3 ground rules (everything else follows from these)

1. **Vertical slice first.** Before building 7 agents, make ONE thin path work end-to-end: idea in → one agent → LLM → result on screen. Every later phase just widens a pipe that already flows. This is the single biggest difference between "finished" and "80% done forever".
2. **Precompute heavy, serve light.** All BERT/BERTopic/Prophet/XGBoost work happens offline in notebooks; results are stored per category. The live app only does lookups + light math + one LLM call. (Feasibility report, Flaw #1.)
3. **Notebook → module → endpoint.** Every agent is built three times, cheaply: explore in a Jupyter notebook (this becomes your report/viva evidence), extract into a clean Python function returning JSON, then expose via FastAPI. Never skip straight to the endpoint.

---

## UX Blueprint (decisions locked 3 Aug 2026)

These three decisions shape the API design, so they are locked before any code:

| Decision | Choice | Consequence for architecture |
| --- | --- | --- |
| **Results delivery** | **Progressive reveal + streamed strategy** — frontend fires the 6 agent calls in parallel; each agent card flips to its real result the moment it finishes; the final strategy text streams in word-by-word via **SSE** | Per-agent endpoints are the real API (not just extras); Agent 7 gets a streaming SSE endpoint; SSE must be proven in the vertical slice (Phase 1) |
| **Guest mode** | **Yes — 1 free analysis without registering**; login required to save history / download PDF / compare | Auth has two tiers: anonymous session (1 rate-limited try, tracked by fingerprint/IP) and JWT user; "Sign up to save this report" becomes the conversion prompt |
| **UX extras (all approved)** | Public landing page · Compare two ideas · Shareable read-only report link · Light/dark theme toggle | All scheduled as Should/Could-have in Phases 4–5; first on the cut list if time runs short |

### Experience principles (applied throughout the phases below)

**Input (Dashboard)**

- **No blank text box:** clickable example-idea chips + optional structured fields (target city, audience, budget range) that feed the planner.
- **Live category preview:** as the user types (debounced), `/api/detect-category` shows "✓ Matched: Food & Restaurants" *before* submit — the category constraint becomes visible intelligence, not a post-submit surprise.
- **Graceful out-of-scope flow:** no match → "Closest match: X — run with X?" The user always chooses; never a dead end, never a silently wrong answer.

**Results (Report)**

- **Executive summary + 4 KPI stat tiles first** (market growth %, price band, sentiment score, competitor count), then detail sections as tabs/accordions — no endless scroll.
- **Data-source badges per section** ("based on ~100K Amazon Grocery reviews") — honesty as a UX feature and a pre-answered examiner question.
- **Actionable next-steps checklist** at the end of every report — "advisor", not just "report".

**Resilience (everywhere)**

- **Partial failure ≠ total failure:** if one agent fails, the other five still render; the failed card shows a retry chip.
- **Rate limits made friendly:** "High demand — retrying with backup model…" (visible Groq fallback), never a silent spinner hang.

---



## Phase 0 — Scope lock & foundations (Week 1)

**Goal: every decision made, every account created, every dataset sampled and on disk.**

- [x] **Supported categories — LOCKED (8), with review-data mapping:**

| Category | Review data source |
| --- | --- |
| Food & restaurants | Yelp (restaurant reviews) |
| Grocery | Amazon `Grocery_and_Gourmet_Food` |
| Beauty & personal care | Amazon `Beauty_and_Personal_Care` |
| Fashion | Amazon `Amazon_Fashion` (+ `Clothing_Shoes_and_Jewelry` if thin) |
| Electronics | Amazon `Electronics` |
| Software / apps | Amazon `Software` |
| E-commerce / retail | Cross-category Amazon sample + retail sales dataset |
| Education | Amazon `Books` (edu segment) + `Software` (edtech) — weakest mapping; goes in the limitations section |

- [ ] Create accounts / keys (all free, no card): Google AI Studio (Gemini key), Groq, Kaggle, HuggingFace, Supabase, GitHub repo. *(Vercel/Render only if the optional deploy stretch ever happens.)*
- [ ] **Dataset acquisition — sampled, never full:**
  - Amazon Reviews 2023: stream the ~6 mapped categories from HuggingFace, keep ~60–100K reviews each → parquet files.
  - Yelp Open Dataset: download tar once, extract ~200K restaurant/service reviews → parquet, delete the rest.
  - Kaggle: Crunchbase startup investments + Indian startup funding (both), Twitter airline sentiment, one retail sales dataset.
  - World Bank: pick 5–10 indicators (GDP growth, sector value-added, internet penetration…), fetch via `wbgapi`.
- [ ] One quick EDA notebook per dataset: row counts, columns, nulls, a couple of plots. (Directly reusable in your project report.)
- [ ] **Start the literature-survey folder** (gap fill): collect 10–15 references (multi-agent systems, BERT sentiment analysis, topic modeling, RAG, AI for business strategy) as you touch each technique — painless now, painful if left for report week. Feeds Review 1.
- [ ] Repo skeleton per the doc's file structure (frontend/, backend/, ai_agents/, data/, vector_db/) + README + .gitignore (exclude data/).

**Definition of done:** `data/` holds ~1–2 GB of clean parquet/CSV samples; 6 EDA notebooks run top to bottom; you can call Gemini and Groq from a 5-line script.

---



## Phase 1 — Vertical slice (Weeks 2–3) ⭐ most important phase

**Goal: a user types an idea in a browser and gets a real, data-grounded strategy paragraph back — streamed.**

Path: React input box → `/api/detect-category` (live preview) → **Customer Insight agent only** (lookup of precomputed sentiment for that category) → Gemini synthesizes a mini-strategy → **streams to the screen via SSE**.

- [ ] Offline: run sentiment (start with VADER; upgrade to DistilBERT later) over Yelp + 1 Amazon category; aggregate per category: top positives, top complaints, sentiment split. Store in Supabase tables.
- [ ] Planner v1 as `/api/detect-category`: keyword/embedding match from free-text idea → supported category + confidence (this same endpoint later powers the live "✓ Matched: …" preview).
- [ ] **DB schema v1, designed before code** (gap fill): `users`, `strategies` (idea, category, report JSON, timestamps), `category_insights` (precomputed per-category agent results), `guest_sessions` (free-try tracking), `share_tokens`. Draw the ER diagram now — it's also a Review-2 deliverable.
- [ ] FastAPI: `/api/customer` returning the real agent JSON, **plus `/api/strategy/stream` — an SSE endpoint that streams the LLM synthesis token-by-token.** CORS on. No auth yet.
- [ ] LLM call via LangChain (current 1.x API) with a provider switch: Gemini primary, Groq fallback — **verify streaming works through both providers.**
- [ ] React: one page — input with live category preview, one agent result card, strategy text streaming in below. Ugly is fine.

**Definition of done:** "I want to start a food delivery startup" shows the matched category while typing, returns real complaint/praise data, and streams a strategy paragraph word-by-word, from the browser.
**Why this order:** it de-risks the 5 scariest unknowns (planner mapping, data→LLM grounding, API wiring, **SSE streaming end-to-end**, rate limits) in week 2 instead of week 7. SSE is in the slice *because* progressive reveal is now a locked UX decision — if it fights us, we find out now, not in Phase 4.

---



## Phase 2 — The five analysis agents (Weeks 4–6)

**Goal: all 6 analysis agents return real JSON. Each follows notebook → module → endpoint.**

Build order (easiest → hardest, ~2–3 days each):


| Order | Agent                                                 | Offline work (notebook)                                                   | Runtime work (light)                                                     |
| ----- | ----------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1     | **Competitor Intelligence**                           | K-Means clusters + Random Forest feature ranking on funding data          | Return competitor table for category                                     |
| 2     | **Market Research**                                   | Prophet/ARIMA forecasts on World Bank + funding time series, per category | Return growth %, trend series, funding summary                           |
| 3     | **Pricing Strategy**                                  | XGBoost price–demand model on retail data; save model + curve points      | Return optimal price band + revenue curve (clearly labeled per-category) |
| 4     | **Social Sentiment** (renamed from "Trend" — Flaw #2) | LDA topics + sentiment on tweets                                          | Return topics, sentiment split, content suggestions                      |
| 5     | **Customer Insight v2**                               | Upgrade VADER → DistilBERT; TF-IDF keywords per category                  | Richer positives/negatives/insights                                      |
| 6     | **Product Innovation**                                | BERTopic on Amazon category reviews → gap themes                          | Return gaps + opportunity list                                           |


- [ ] Shared output contract first: every agent returns `{agent, category, status, headline, metrics{}, chart_data[], insights[], source{dataset, sample_size}}` — `status` drives the card states (running/done/failed), `source` drives the data-source badges, and the whole contract makes frontend and Agent 7 trivial.
- [ ] Endpoints `/api/market`, `/api/competitor`, `/api/customer`, `/api/trends`, `/api/pricing`, `/api/innovation` — **these are the progressive-reveal API: the frontend fires all six in parallel and flips each card as its response lands.** Keep `/api/analyze` as a convenience aggregator (used by guest mode, PDF, and tests).
- [ ] Per-agent error handling: an agent failure returns a clean `{status: "failed", retryable: true}` — never a 500 that kills the whole run (partial-failure UX depends on this).
- [ ] **Contract tests, pytest** (gap fill): for each agent × each of the 8 categories, assert schema-valid JSON (required fields, types, non-empty insights). Cheap to write, catches every future refactor, and becomes the backbone of the report's Testing chapter.
- [ ] Record accuracy/quality metrics in each notebook (silhouette score, MAPE, R², topic coherence) — examiners ask for these.

**Definition of done:** all six per-agent endpoints return contract-conformant JSON for every supported category in seconds (including clean failure JSON when a dependency is down); 6 notebooks with metrics checked in.

---



## Phase 3 — RAG + Strategy Generation Agent (Week 7)

**Goal: Agent 7 — the master synthesis with retrieval grounding.**

- [ ] Embed ~100–300K sampled review chunks (MiniLM, `sentence-transformers`) → FAISS index on disk.

> Decision applied: with **local demo** as the evaluation target, FAISS + local MiniLM on your laptop *is* the final architecture — no RAM constraint. If a public URL is ever wanted later, the documented swap is Supabase **pgvector** + Gemini's free embedding API for query embedding (zero backend RAM); mention it in the report as the "deployment path" — free viva marks.
- [ ] RAG: retrieve top-k review snippets relevant to the user's idea; inject as "voice of the customer" evidence.
- [ ] Master prompt: structured sections (Executive Summary, Market, Competitors, Customers, Pricing, Innovation, Go-to-Market, Risks, **Next Steps checklist**) + require citing which agent each claim came from.
- [ ] Structured output with a streaming-friendly format: section markers stream through `/api/strategy/stream` (SSE, built in Phase 1) so the report renders section-by-section as it generates; a final Pydantic-validated JSON version is stored for history/PDF/share.
- [ ] Executive-summary KPIs extracted into 4 stat-tile values (market growth %, price band, sentiment score, competitor count) as first-class fields in the stored JSON.
- [ ] Cache reports in Supabase (idea+category hash) — saves rate limits, makes demos instant, and powers the guest-mode free try cheaply.

**Definition of done:** one call → full multi-section strategy report streaming live, grounded in agent outputs + retrieved review quotes, for 3+ different test ideas; stored JSON validates.

---



## Phase 4 — Auth, guest mode + real frontend (Weeks 8–9)

**Goal: the app looks like the doc's screenshots and behaves per the UX Blueprint.**

- [ ] JWT auth: register/login/refresh (FastAPI + passlib/bcrypt + python-jose), users table in Supabase, protected routes in React (AuthContext), token in Axios interceptor.
- [ ] **Guest mode:** anonymous visitors get 1 free analysis (rate-limited by IP/fingerprint, served from cache when possible); "Sign up to save & download" prompt on the guest report; history/PDF/compare stay behind login.
- [ ] Pages: Login, Register, Dashboard, Analyze, Report — built to the UX Blueprint:
  - Dashboard: example-idea chips + optional structured fields (city, audience, budget) + live category preview (`/api/detect-category`, debounced) + graceful out-of-scope chooser.
  - Analyze: **real progressive reveal** — 6 agent cards fed by their own parallel requests (Idle → Running → real headline result or failed-with-retry-chip), then the strategy streaming in below.
  - Report: executive summary + 4 KPI stat tiles up top; detail sections as tabs/accordions; data-source badge on every section; next-steps checklist at the end.
- [ ] Charts (Recharts): market growth line, competitor table, pricing curve, sentiment donut, trending topics — all fed by `chart_data` from the shared contract.
- [ ] Resilience states: partial-failure rendering, friendly rate-limit message with visible Groq fallback, empty/loading skeletons.
- [ ] **Card pacing** (gap fill): precomputed agents answer in <1 s, which would make the progressive reveal invisible — stagger card flips ~0.6–0.9 s apart; the genuinely slow part (the streaming strategy) provides the real suspense. Standard skeleton-state pacing — be ready to say exactly that in the viva.
- [ ] **Robustness & security pass** (gap fill, viva gold): input length caps + sanitization; user text wrapped in delimiters inside LLM prompts (prompt-injection guard); `slowapi` rate limiting on analyze + auth endpoints; expired-JWT handled gracefully in the UI (auto-logout with a message, not a broken page).
- [ ] Tailwind styling: dark sidebar, glassmorphism cards, Framer Motion transitions. Responsive. **Light/dark theme toggle** (dark default; light theme doubles as the print/PDF-friendly view).

**Definition of done:** a guest runs one full analysis watching cards flip in real time and the strategy stream; signs up mid-flow without losing the report; logged-in user sees every chart live; killing one agent's endpoint still yields a 5/6 report with a retry chip.

---



## Phase 5 — History, PDF + UX extras (Week 10)

- [ ] Strategy history: list + reopen past reports (Supabase `strategies` table).
- [ ] PDF export — **decision: client-side capture** (html2canvas of the rendered light-theme report + jsPDF), so the PDF matches exactly what the user sees and no server-side chart re-rendering is needed. reportlab stays the fallback if capture quality disappoints.
- [ ] **Disclaimer footer** on web report + PDF (gap fill): "AI-generated strategic guidance based on sampled historical datasets — not professional financial advice." (Ethics point examiners reward.)
- [ ] **Shareable report link:** read-only public route `/r/{token}` serving the stored report JSON — no login needed to view, no edit/rerun controls.
- [ ] **Compare two ideas:** pick 2 saved strategies → side-by-side table of KPIs (market %, price band, sentiment, competitor count) + both executive summaries. Needs history, hence this phase.
- [ ] **Public landing page:** hero ("Type an idea. Get a strategy."), how-it-works (3 steps, 7 agents), link to a live sample report (a shareable link!), and the guest-mode CTA "Try one free analysis".
- [ ] Final pass on empty/error/loading states; out-of-scope idea UX polished.

**Definition of done:** generate → download PDF → share the link from another browser (logged out) → compare it against a second idea → log out/in → history still there. Landing page is the app's front door.

---



## Phase 6 — Demo, final report + viva prep (Week 11)

Deployment is **out of the critical path** (decision: local demo). The final week goes to what's actually graded.

- [ ] **Demo environment hardening (local):** one-command startup script (backend + frontend + seeded DB), verified on a cold reboot; offline tolerance — cached flagship reports render fully even if Wi-Fi or LLM quota dies mid-demo.
- [ ] **Demo kit:** 3 pre-generated flagship reports (cached), 5 rehearsed test ideas, a 5-minute demo script — **open with the guest flow:** landing page → free try → cards flipping live → strategy streaming. No login fumbling in front of examiners.
- [ ] **Manual E2E checklist + test-case table** (gap fill — the ID/scenario/expected/actual/pass-fail format college reports want): auth flows, all 8 categories, out-of-scope idea, one-agent-down, guest limit, rate-limit fallback, PDF, share link, compare.
- [ ] **Final report assembly** — chapters map 1:1 to artifacts you already have (see Academic Deliverables Track below): architecture diagram, dataset table with *honest* sampled sizes, per-agent metrics table, "precompute heavy / serve light" pattern explanation, **data licensing & ethics section** (gap fill: Yelp academic-use terms, dataset citations, AI-content disclaimer), limitations (category constraint, dataset vintage, education-category mapping) — stating limitations yourself earns marks and disarms examiners.
- [ ] **Viva Q&A sheet:** 20 likely questions with your answers (why JWT, why precompute, why sampling is honest, how RAG grounds the LLM, what pgvector would change…).
- [ ] *(Optional stretch — only if everything above is done):* public deploy: Vercel + Render + the pgvector/Gemini-embeddings swap noted in Phase 3.

**Definition of done:** cold-reboot laptop → one command → full demo runs, offline-tolerant; final report submitted; viva sheet written; demo rehearsed once end-to-end.

---



## Academic Deliverables Track (gap fill — runs alongside the build)

Decision: your college requires **staged reviews (2–3)** + a **college-format final report**. Anchor exact dates when announced; each review is fed by artifacts the phases already produce — never build documents from scratch.

| Checkpoint | Typical timing | What's due | Produced by |
| --- | --- | --- | --- |
| **Review 1** | ~Week 3–4 | Abstract, problem statement, objectives, high-level architecture, initial literature survey | Phase 0 EDA + reference folder; architecture from the feasibility report; Phase 1 slice as proof-of-concept |
| **Review 2** | ~Week 7–8 | Design diagrams (use-case, class/module, sequence, DFD, ER) + partial working demo | ER diagram from Phase 1 schema task; sequence diagram = the progressive-reveal flow; demo = slice + 3–4 agents |
| **Review 3 / Final** | ~Week 11+ | Full demo, test results, final report, viva | Phase 6 outputs |

*(If reviews turn out to need slide decks, each row above is the slide outline — no separate prep task.)*

Final report chapter → artifact mapping (nothing gets written twice):

| Report chapter | Source artifact |
| --- | --- |
| Literature survey | Phase 0 reference folder |
| SRS / requirements | UX Blueprint + Decision Log |
| System design | Architecture diagram + ER/UML/DFD from Reviews 1–2 |
| Implementation | Agent notebooks + module structure |
| Testing | Contract tests (Phase 2) + E2E test-case table (Phase 6) |
| Results & discussion | Per-agent metrics + sample reports + screenshots |
| Limitations & future work | Limitations list + pgvector deploy path + live-trends stretch goal |

---

## Cut list (MoSCoW) — decide *now* what dies if time runs short


| Priority            | Items                                                                                                                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Must have**       | Vertical slice (incl. SSE streaming), all 7 agents (even simplified), progressive-reveal agent cards, live category preview + out-of-scope chooser, custom JWT auth, dashboard + report pages (KPI tiles + tabs), 2–3 charts, partial-failure handling, notebooks with metrics, agent contract tests, **review deliverables on schedule** |
| **Should have**     | All 5 chart types, PDF export, history, guest mode (1 free try), data-source badges, next-steps checklist, security/robustness pass                                                                                                            |
| **Could have**      | Landing page, shareable report link, compare two ideas, light/dark theme toggle, Framer Motion polish, forgot-password, live pytrends/Reddit signal, **public deployment (Vercel + Render + pgvector swap)**                                   |
| **Won't have (v1)** | Real-time social scraping, full datasets, GPU anything, refresh-token rotation, mobile-perfect UI, WebSocket live agent logs, IEEE paper                                                                                                       |


Rule: when behind schedule, cut from the bottom. Never cut the vertical slice or the notebooks.
Escape hatch: if SSE streaming misbehaves in Phase 1, the approved fallback is *progressive agent cards + non-streamed strategy text* (cards still flip live; only the word-by-word effect is dropped). Decide by end of Phase 1, not later.

---



## Decision Log — everything locked 3 Aug 2026, nothing left open

| # | Decision | Choice | Applied in |
| --- | --- | --- | --- |
| 1 | Results UX | Progressive reveal (6 parallel per-agent calls flip cards live) + SSE-streamed strategy text; fallback = non-streamed text if SSE fights us in Phase 1 | UX Blueprint; Phases 1–4 |
| 2 | Guest mode | Yes — 1 free analysis without login; save/PDF/compare behind login | Phase 4 |
| 3 | UX extras | All four approved: landing page, compare two ideas, shareable link, theme toggle | Phases 4–5; Could-have tier |
| 4 | Timeline | ~3 months at 10–15 hrs/wk → 11 weeks + ~2 weeks buffer (start ≈ mid-Aug, final ≈ mid-Nov 2026) | Header; phase weeks |
| 5 | LLM provider | Gemini Flash free (primary) + Groq Llama 3.3 70B (fallback); report describes an "LLM-agnostic architecture" | Phases 1, 3; rate-limit UX |
| 6 | Categories | The 8: food & restaurants, e-commerce/retail, beauty, software/apps, grocery, fashion, electronics, education | Phase 0 mapping table |
| 7 | Social agent | Honest reframe only ("Social Sentiment Agent"); live trends stays Could-have | Phase 2 |
| 8 | Auth | Custom JWT (FastAPI + passlib/bcrypt + python-jose), per the original doc | Phase 4 |
| 9 | Deployment | **Local demo is the evaluation target**; public deploy = optional stretch (pgvector + Gemini embeddings swap documented) | Phase 3 note; Phase 6 |
| 10 | Team framing | Officially solo — report presents one member owning all four layers | Academic track; viva story |
| 11 | Academic deliverables | Staged reviews (2–3) + college-format final report; no PPT/IEEE requirements known | Academic Deliverables Track |

**Next milestone:** when your college announces review dates, anchor the Academic Deliverables Track to real dates. Otherwise — ideation is complete; the next step is Phase 0.

