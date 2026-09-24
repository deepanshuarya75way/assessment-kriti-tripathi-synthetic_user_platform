# Final Report — Synthetic User Research Platform upgrade

## 1. What I changed
Transformed a ~600-line single-package LangGraph + Streamlit prototype into a
full-stack, production-style application **without discarding the working AI logic**.
The four-agent pipeline, structured Pydantic output, per-persona isolation, PDF
report and persona chat were all preserved and moved behind a proper API, database,
auth layer and React frontend. Every phase in the brief (audit → architecture →
backend → AI → frontend → tests → devops → docs → review) was completed.

## 2. New architecture
Modular monolith: **React/TypeScript SPA → FastAPI (api → service → repository →
model) → SQLAlchemy → SQLite/PostgreSQL**, with the preserved **LangGraph** pipeline
and a centralized LLM service behind the service layer. Long AI runs execute as a
FastAPI background task with real `PENDING→RUNNING→COMPLETED/FAILED` status. Full
detail in `docs/architecture.md`.

## 3. Backend technologies
FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.0, Alembic, PyJWT, passlib/bcrypt,
reportlab, LangGraph/LangChain. Layered: `api/v1`, `services`, `repositories`, `models`,
`schemas`, `graph`, `agents`, `report`, `core`.

## 4. Frontend technologies
React 18, TypeScript, Vite, React Router. Typed API client mirroring backend schemas,
auth context, toast + confirm-dialog components, loading/empty/error states, live status
polling, pagination, PDF download, responsive CSS with light/dark support.

## 5. Database design
9 tables: `users`, `research_projects`, `personas`, `survey_questions`,
`survey_responses`, `insight_reports`, `themes`, `conversations`,
`conversation_messages`. UUID PKs, cascade-delete FKs, one-to-one report, responses
flattened to (persona, question) rows, JSON columns for simple lists, indexes on all
lookups. ER diagram + rationale in `docs/database.md`. Alembic migration included.

## 6. AI architecture
Preserved four-agent LangGraph pipeline (Persona → Survey → Response → Insight).
Improvements: duplicate-persona detection, response-count reconciliation, survey
structural validation, and a **centralized LLM service** with retry, model fallback,
timeout and structured tracing. Added a config-selected **fake provider** for offline
runs and tests. Fixed the original `MemorySaver` lifecycle bug by making the DB the
source of truth for run recovery (documented in `docs/design-decisions.md`).

## 7. Authentication / security
JWT bearer auth; bcrypt-hashed passwords (never plaintext). Every research route scoped
to the owner; cross-user access returns 404 (no existence leak). Uniform error envelope
(no stack traces to clients), input length caps + count bounds, explicit CORS allow-list,
secrets only via env vars (never in DB or logs).

## 8. Testing
49 pytest tests, **~94% backend coverage**: schema validators, security (hash/JWT/expiry),
LLM (success/retry/fallback/None/total-failure via stubs), agents/pipeline, repositories
(CRUD/relationships/cascade), API (auth/research lifecycle/artifacts/PDF), authorization
(cross-user, unauthenticated), chat persistence, and PDF generation. No test touches a
real network/LLM.

## 9. CI/CD
GitHub Actions: backend job runs ruff, black --check, mypy, alembic upgrade, and pytest
with coverage; frontend job runs TypeScript type-check + Vite build. Runs on push/PR.

## 10. Docker / deployment
`backend/Dockerfile` (non-root, healthcheck, migrate-then-serve), `frontend/Dockerfile`
(multi-stage build → nginx serving static + proxying `/api`), and `docker-compose.yml`
(Postgres + backend + frontend). `docker compose up --build` runs the whole stack offline.

## 11. Important bugs fixed
- **MemorySaver lifecycle (B1):** graph rebuilt a fresh in-memory checkpointer per call, so
  run recovery never worked. Fixed via compile-once + DB-backed persistence.
- **Secret var mismatch (B3):** docs/`.env` referenced `ANTHROPIC_API_KEY` while code used
  OpenRouter. Now consistent (`OPENROUTER_API_KEY`) and centralized in config.
- **No durability (B2):** results were lost on exit — now fully persisted.
- **No response-count validation (B4):** added reconciliation so counts always match.
- **No duplicate/persona-structure validation (B5/B6):** added dedup + schema validators.

## 12. Files created/modified
~90 source files across `backend/` (app + tests + alembic + scripts), `frontend/` (SPA),
`docs/` (4 docs + 7 screenshots), plus Docker, CI, `.env.example`, `.gitignore`, LICENSE,
`PROJECT_AUDIT.md`, README. Git history is organized into 9 logical commits.

## 13. How to run
Docker: `cp .env.example .env && docker compose up --build` → http://localhost:8080.
Local: backend `pip install -r requirements-dev.txt && python -m scripts.seed && uvicorn app.main:app --reload`;
frontend `npm install && npm run dev` → http://localhost:5173. Defaults to offline fake-LLM
mode (no API key). Full steps in README.

## 14. How to run tests
`cd backend && pytest --cov=app --cov-report=term-missing` (49 tests). Quality gates:
`ruff check . && black --check . && mypy app`.

## 15. Known limitations (honest)
Personas are synthetic (exploratory, not representative) — surfaced everywhere. The AI run
is an in-process background task (single-instance; queue/workers documented as the scale
path, not built). No performance benchmarks are claimed because none were measured. Fake
mode returns deterministic placeholder content; real quality depends on the configured model.

## 16. Interview questions to prepare
See `docs/interview-preparation.md` — architecture, backend request flow, DB schema/indexes,
LLM validation/retry/fallback, preventing persona context mixing, auth/authorization,
LLM mocking, CI, and the honest scaling story. All answers are grounded in this code.

## 17. Suggested resume bullets (strictly from what's implemented)
- Built a full-stack AI research platform (FastAPI + React/TypeScript + PostgreSQL) that
  orchestrates a 4-agent LangGraph pipeline to generate synthetic personas, surveys and
  insights, with persistent runs and real status tracking.
- Designed a layered backend (API/service/repository) with a 9-table relational schema,
  Alembic migrations, JWT auth and per-user authorization.
- Implemented a centralized LLM service with retry, model fallback, timeouts and an offline
  deterministic provider; achieved ~94% backend test coverage (49 tests) with fully mocked LLMs.
- Set up CI (ruff/black/mypy/pytest + TypeScript build) and a Dockerized Postgres/backend/
  frontend stack runnable with one command.
