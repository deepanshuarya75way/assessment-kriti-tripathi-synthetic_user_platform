# Project Audit — Synthetic User Research Platform

**Date:** 2026-09-24
**Auditor:** Senior engineer review, prior to the production upgrade.
**Scope:** Audit of the existing `synthetic_persona_platform` codebase before any
major change, per the "understand before rewriting" rule. This document is the
Phase 1 deliverable; it drives every later phase.

---

## 1. Current architecture (as inspected)

The original project is a **single-package Python script collection** of ~600
lines. There is no service boundary, no persistence, and no HTTP layer — it runs
either as a CLI (`main.py`) or a Streamlit app (`streamlit_app.py`).

```
streamlit_app.py / main.py     (entry points)
        │
        ▼
   graph.run_pipeline()         (LangGraph StateGraph, compiled per call)
        │
        ├─ persona_agent_node   ─┐
        ├─ survey_agent_node     │  each node calls llm.invoke_structured(...)
        ├─ response_agent_node   │  → OpenRouter (OpenAI-compatible) chat API
        └─ insight_agent_node   ─┘
        │
        ▼
   report_generator.generate_pdf_report()   (reportlab → local .pdf)

agents/interview_agent.py       (two chat-memory session classes, used by UI/CLI)
schemas.py                      (Pydantic models = LLM structured-output targets)
state.py                        (TypedDict GraphState flowing through the graph)
llm.py                          (centralized LLM client + retry/fallback)
```

**Data flow today:** all state lives in-process in a `GraphState` `TypedDict`
that LangGraph threads node-to-node. Nothing is written to disk except the
generated PDF. When the process exits, all personas/surveys/insights are gone.

---

## 2. Existing features

| Feature | Status |
|---|---|
| Persona generation (one call per persona, diversity-aware) | Works |
| Survey generation (typed questions, calibrated to personas) | Works |
| Response simulation (per-persona isolated calls) | Works |
| Insight extraction (themes/sentiment/risks/recommendations) | Works |
| PDF report (reportlab, XML-escaped) | Works |
| Persona chat (memory-carrying, isolated per session) | Works |
| Placement mock-interview bonus (interviewer persona + feedback) | Works |
| Centralized LLM service with retry + model fallback | Works |
| Streamlit UI (form, persona cards, chat, PDF download) | Works |

---

## 3. Existing strengths (things worth preserving)

1. **Structured LLM output via Pydantic + `with_structured_output`.** No fragile
   regex/JSON parsing. This is the single best decision in the codebase.
2. **Centralized LLM abstraction (`llm.py`).** All calls go through
   `invoke_structured` / `invoke_chat` with retry and model fallback. Correctly
   treats a silent `None` (model answered in prose instead of calling the tool)
   as a failure.
3. **Persona isolation in response generation.** Each persona answers in its own
   LLM call, so voices don't bleed together. IDs are forcibly re-stamped after
   generation so a hallucinated `id` can't corrupt downstream joins.
4. **Single-responsibility agents.** Each node does exactly one thing and reads a
   shared, typed state. Clean to test and reason about.
5. **Honest documentation.** The existing README and docstrings are candid about
   trade-offs (e.g. why personas are generated one at a time). This honesty is
   carried forward.
6. **PDF safety.** Dynamic text is XML-escaped before going into reportlab
   paragraphs — an existing, correct injection guard.

---

## 4. Bugs and correctness issues

| # | Severity | Issue |
|---|---|---|
| B1 | High | **`MemorySaver` lifecycle bug.** `build_graph()` creates a *new* `MemorySaver()` on every call, and `run_pipeline()` / `get_run_history()` each call `build_graph()`. The checkpointer therefore never outlives a single `invoke`, so `get_run_history(thread_id)` reads back an **empty** state for any run created by a different `build_graph()` call. The README's "resume a run" claim does not actually hold. (Spec §8.) |
| B2 | High | **No durable persistence at all.** Restarting the process loses every result. There is no way to list past research or reopen a run. |
| B3 | Medium | **README ↔ code mismatch on secrets.** README/`main.py`/`.env.example` all reference `ANTHROPIC_API_KEY`, but `llm.py` reads `OPENROUTER_API_KEY`. A reviewer following the README cannot run the project. (Spec §30.) |
| B4 | Medium | **No cross-persona response-count validation.** If a model returns answers for the wrong questions, or drops answers, nothing detects it; the insight agent silently analyzes malformed data. (Spec §13.) |
| B5 | Medium | **No duplicate-persona detection.** Diversity relies entirely on prompt wording; identical personas are accepted. (Spec §11.) |
| B6 | Low | **No survey-question structural validation.** A `multiple_choice` question with no `options` is accepted. (Spec §12.) |
| B7 | Low | **Blocking, unbounded pipeline.** `run_pipeline` runs synchronously; in Streamlit the whole UI blocks for minutes with no progress state. |

---

## 5. Technical debt / architectural weaknesses

- **Flat module namespace** (`from schemas import ...`, `from state import ...`).
  Not importable as a package; collides easily; no clear layering.
- **Business logic wired directly to entry points.** No API, no service layer,
  no repository layer — impossible to reuse the pipeline behind HTTP without
  refactoring.
- **No configuration object.** Env vars are read ad hoc inside `llm.py`.
- **Logging is partial** — agents log failures but there is no structured,
  leveled, request-scoped logging across a run.
- **No tests and no CI.** Nothing guards against regressions.
- **Output directory** written relative to source; no notion of per-run storage.
- **`get_llm()` dead-ish path** bypasses retry/fallback; easy to misuse.

---

## 6. Security issues

| # | Issue | Plan |
|---|---|---|
| S1 | No authentication/authorization — anyone can run/read anything. | ADD JWT auth; scope all data to the owning user. |
| S2 | No input size limits — a huge product description = a huge (costly) prompt. | ADD max-length validation + configurable caps. |
| S3 | Errors surfaced raw to the UI (`st.error(f"...: {e}")`) can leak internals. | ADD uniform error envelope; safe client messages, detailed server logs. |
| S4 | No CORS policy (will matter once a separate frontend exists). | ADD explicit CORS allow-list from config. |
| S5 | Secrets only in `.env` — but README committed the wrong var name; risk of confusion/leak. | Fix `.env.example`, enforce `.gitignore`, never store keys in DB. |
| S6 | `HTTP-Referer: http://localhost` header hard-coded. | Move to config. |
| — | (Good) PDF text is already escaped; no SQL yet so no SQLi today. | Keep parameterized ORM going forward. |

---

## 7. Gaps vs. a production SDE project

- **Backend:** no REST API, no status/run model, no service/repository split.
- **Database:** none. No entities, relationships, migrations, or persistence.
- **Frontend:** Streamlit only — fine as a demo, not a portfolio SPA.
- **Testing:** none (unit, API, DB, or mocked-LLM).
- **CI/CD:** none.
- **Docker:** none.
- **Docs:** a good README, but no architecture/database/design-decision/interview docs.
- **Observability:** no run IDs, durations, or structured agent logs.

---

## 8. Recommended target architecture

A **modular monolith** (no microservices — spec §39):

```
Frontend (React + TS + Vite SPA)
        │  REST / JWT
        ▼
FastAPI backend
  ├─ api/v1        (thin routers: validation, status codes, error envelope)
  ├─ services      (business logic: research orchestration, auth)
  ├─ repositories  (all DB access; no ORM leakage into routers)
  ├─ models        (SQLAlchemy ORM)
  ├─ graph/agents  (the PRESERVED LangGraph pipeline + centralized LLM service)
  ├─ report        (reportlab PDF, unchanged in spirit)
  └─ core          (config, logging, security, exceptions)
        │
        ▼
SQLAlchemy → SQLite (dev/test) / PostgreSQL (docker-compose)
```

**Run execution:** the pipeline runs as a FastAPI background task; the DB row's
`status` moves `PENDING → RUNNING → COMPLETED/FAILED`. This is honest (no fake
progress) and avoids a synchronous multi-minute request, without introducing
Celery/Redis (documented as the scale path only).

**LangGraph memory fix (B1):** the **database becomes the source of truth** for
cross-run recovery. The in-memory checkpointer is used only within a single run;
durability and history come from persisted rows. This is documented in
`docs/design-decisions.md`.

**Offline/fake-LLM mode:** a config-selected fake LLM provider returns
deterministic structured data so the whole app runs end-to-end without an API
key. This powers the test suite and lets a reviewer try the product offline. It
is clearly labelled and never presented as real research.

---

## 9. Migration plan (KEEP / IMPROVE / REFACTOR / ADD / REMOVE)

### KEEP (move verbatim or nearly so)
- `schemas.py` LLM models → `app/graph/schemas.py` (these are the structured-output contracts).
- The four agent prompts and per-persona isolation logic → `app/agents/*`.
- `interview_agent.py` chat-session design → `app/agents/interview_agent.py`.
- `report_generator.py` reportlab logic (with the escaping) → `app/report/generator.py`.
- Centralized LLM service concept → `app/graph/llm.py`.

### IMPROVE
- LLM service: add timeout, token/usage capture, run-scoped tracing/logging, a fake provider, config-driven models.
- Agents: add duplicate-persona detection, survey structural validation, response-count validation.
- PDF: add the synthetic-data disclaimer (spec §14/§31); graceful failure.

### REFACTOR
- Flat modules → layered package (`api/service/repository/model`).
- `run_pipeline` → `ResearchService.run(...)` that persists each stage to the DB.
- Config → `app/core/config.py` (pydantic-settings), single source of env vars.

### ADD
- SQLAlchemy models + Alembic migrations; repositories; DB-backed run status.
- FastAPI app: auth, research CRUD, personas/survey/responses/insights/report/chat endpoints; error envelope; structured logging; request IDs.
- JWT authentication + per-user authorization.
- React + TypeScript frontend (all pages) talking to the API.
- pytest suite (unit/API/DB/mocked-LLM/authz); GitHub Actions CI; Docker + compose; docs.

### REMOVE
- Wrong `ANTHROPIC_API_KEY` references (replace with `OPENROUTER_API_KEY`).
- Hard-coded example inputs in `main.py` as the *only* entry point (kept as an optional seed/demo script).
- Generated artifacts (`output/*.pdf`) from version control.
- Streamlit is **not deleted** — it is retained as a documented lightweight dev/demo UI (spec §32), reusing the same service layer.

---

## 10. Risks called out for honesty (spec §43)

- Synthetic personas are **not** real users; every report and the UI must say so.
- No performance benchmarks are claimed; none are measured, so none are stated.
- Background-task execution is single-process; true horizontal scale (queue +
  workers) is documented as future work, not implemented.
