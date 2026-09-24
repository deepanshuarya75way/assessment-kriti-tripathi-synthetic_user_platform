# Interview preparation

Questions an interviewer might ask about this project, with answers grounded **only**
in what is actually implemented here. Be ready to open the file that backs each answer.

## Architecture

**Why this architecture?**
A modular monolith: one FastAPI backend with clear internal layers (api → service →
repository → model), a React SPA, and a relational DB. The domain is small and cohesive,
so a monolith keeps the AI pipeline, persistence and API in one boundary. Microservices
would add operational cost with no benefit here.

**Why LangGraph and not one large prompt?**
Four sequential stages share state (personas → survey → responses → insights). LangGraph
models that as a typed state graph with one node per stage — explicit, testable, and easy to
extend. One giant prompt would be unreliable (truncation, mixed concerns) and hard to debug.

**Why FastAPI?**
Native Pydantic validation, automatic OpenAPI docs, async support, and a clean typed REST
boundary between the SPA and backend.

**Why a relational database, and SQLite vs PostgreSQL?**
The data is relational (projects own personas/questions/responses/report; reports own themes;
personas own conversations). SQLite gives zero-setup local dev/tests; PostgreSQL is the Docker
target. Same models and migrations on both.

## Backend

**How does a request travel through the backend?**
Router (validate + auth dependency) → service (business logic) → repository (SQL) → DB, and
back through Pydantic response models. Routers hold no business logic; repositories are the only
code that runs ORM queries. Example: `POST /research` → `ResearchService.create` → persists
`PENDING` → schedules a background run → returns 201.

**How do you run the long AI job without blocking the request?**
A FastAPI `BackgroundTasks` job (`execute_research_run`) with its own DB session. It moves the
project through `RUNNING → COMPLETED/FAILED`; the SPA polls `GET /research/{id}` for real status.

**How do you validate requests?**
Pydantic schemas on every endpoint: types, length caps on free-text, and persona/question count
bounds. Invalid input returns a 422 in the uniform error envelope.

**How do you structure services and repositories?**
Services orchestrate (auth, research lifecycle, chat) and never touch SQL directly. Repositories
(`UserRepository`, `ResearchRepository`, `ConversationRepository`) own all queries. This keeps
business logic unit-testable without HTTP.

**How do you handle errors?**
Custom exceptions map to a single envelope `{"success":false,"error":{"code","message"}}`.
Internal details (stack traces, model errors) are logged server-side; clients get safe messages.
A catch-all handler returns a generic 500 for anything unexpected.

## Database

**Explain the schema / relationships.**
See [database.md](database.md). `User 1—* ResearchProject 1—* {Persona, SurveyQuestion,
SurveyResponse}` and `1—1 InsightReport 1—* Theme`; `Persona 1—* Conversation 1—*
ConversationMessage`. All children cascade-delete with their parent.

**Why flatten survey responses?**
The LLM returns *persona → list of answers*. Storing one row per (persona, question) makes
responses queryable and aggregatable (e.g. sentiment per question) instead of an opaque blob.

**What indexes would you add / did you add?**
Implemented: unique `users.email`; `research_projects.owner_id` and `.status` (list + dashboard);
every child `project_id`; `survey_responses.question_id`/`persona_slug`; chat FKs. Next under load:
composite `(owner_id, created_at)` for paginated history.

**How would the database scale?**
Read replicas for list/dashboard queries; partition or archive old projects; the JSON columns
could move to typed tables if query patterns demand it. Connection pooling is already configured
for PostgreSQL.

## AI

**How do you validate LLM output?**
`with_structured_output(PydanticSchema)` forces schema-conformant output, validated on arrival.
Schema validators enforce rules (multiple-choice needs ≥2 options; confidence clamped to [0,1]).

**What happens if the model fails? How do retries/fallback work?**
The centralized LLM service retries each model N times with backoff, then falls back to the next
model; only if all fail does it raise. A silent `None` (model replied in prose instead of calling
the tool) is treated as a failure too. This is covered by unit tests using stub chains.

**Why fallback models?**
Free/hosted model slugs get deprecated or rate-limited without warning; falling back keeps the
pipeline working instead of hard-failing on one slug.

**How do you prevent persona context mixing?**
Each persona answers in its own isolated LLM call — no shared context. IDs are re-stamped after
generation so a hallucinated id can't corrupt joins, and responses are reconciled against the
actual question set (extras dropped, missing back-filled) so counts always match.

**How do you handle hallucinations / are synthetic personas real users?**
They are explicitly **not** real users. The insight prompt is instructed to treat responses as
synthetic and exploratory, and the disclaimer appears in the UI, the API response and the PDF.
Structured schemas bound what the model can return.

## Security

**Where are API keys stored?**
In environment variables only (`.env`, git-ignored), read once via a settings object. Never in the
database, never logged, never returned to clients.

**How is authentication handled?**
Bcrypt-hashed passwords; stateless JWT access tokens (PyJWT) carrying the user id. A bearer
dependency resolves the current user on protected routes.

**How do you prevent users accessing others' projects?**
Every research query is scoped by `owner_id` in the service layer. A project owned by someone else
returns **404** (not 403) so existence isn't leaked. This is covered by authorization tests.

**Other hardening?**
Uniform error envelope (no stack traces to clients), input length caps, explicit CORS allow-list,
and count/length bounds as cost controls.

## Testing

**How do you test LLM-based functionality? Why mock the LLM?**
A deterministic `fake` provider returns schema-valid data with no network call. Mocking keeps tests
fast, hermetic, free and reproducible. Retry/fallback/failure paths are tested with stub chains that
fail a set number of times.

**What does your CI pipeline do?**
GitHub Actions runs, on push/PR: ruff (lint), black (format check), mypy (types), Alembic upgrade,
and pytest with coverage for the backend; and TypeScript type-check + Vite build for the frontend.

**Coverage?**
~94% on the backend (49 tests: schemas, security, LLM, agents, repositories, API, authz, chat, PDF).

## Scalability

**What if 1,000 users run research simultaneously?**
Today the run is an in-process background task — fine for one instance, not for that load. I'd move
the run step to a task queue (Redis + workers), keep the API stateless behind a load balancer, and
let workers autoscale. The architecture already isolates the run behind a service call, so this is a
contained change. See [architecture.md](architecture.md).

**Would you use background workers / Redis / a queue?**
Yes — as the scale path, not prematurely. I deliberately did not add Celery/Redis now because a single
instance doesn't need it; adding it would be over-engineering. I documented the trade-off instead of
faking it.

**How would you control LLM cost?**
Already: configurable model, persona/question caps, input-length limits, retry limits, timeouts.
Next: cache identical (product, audience) inputs; batch where safe; per-user quotas.

## Honesty checklist (be ready to say what is NOT done)
- No real-user data — personas are synthetic; results are exploratory.
- No measured performance benchmarks (so none are claimed).
- No queue/worker infrastructure yet (documented, not implemented).
- `fake` mode returns placeholder content; real quality depends on the configured model.
