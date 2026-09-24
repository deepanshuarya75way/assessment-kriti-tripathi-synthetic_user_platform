# Design decisions

Only decisions actually implemented in this repository are documented here.

## Why LangGraph?
The workflow is four sequential AI stages that share state (personas feed the survey,
which feeds responses, which feed insights). LangGraph models exactly this — a typed
`StateGraph` where each node reads/writes a shared state — giving an explicit, testable
pipeline instead of ad-hoc function chaining, with a clean place to add branching later.

## Why Pydantic structured output?
Every agent uses `llm.with_structured_output(Schema)` so the model must return data
matching a schema, validated on arrival. This removes fragile regex/JSON parsing and
means malformed model output fails fast at the boundary instead of corrupting downstream
logic. Schemas also encode rules (e.g. `multiple_choice` requires ≥2 options; confidence
is clamped to [0,1]).

## Why separate agents (not one big prompt)?
Single responsibility. Each agent has one job, one prompt, and is independently testable
and debuggable. It also improves reliability: personas are generated one per call, because
asking a small/free model to emit every rich field for many personas at once frequently
truncates and drops required fields.

## Why generate personas individually?
Smaller output per call → far fewer truncation/validation failures on free models. The
cost is one extra call per persona; each prior persona is summarized back into the prompt
so the next stays distinct, and a lightweight duplicate check retries near-duplicates.

## Why a centralized LLM service?
All calls go through `invoke_structured` / `invoke_chat`, which own retry, model fallback,
timeout, and structured tracing. Provider configuration lives in one place. This avoids
duplicated client setup and gives consistent failure handling — including treating a silent
`None` (model answered in prose instead of calling the tool) as a failure to retry/fail over.

## Why a `fake` LLM provider?
A config-selected deterministic provider returns schema-valid data with no network call.
It makes the test suite fast, hermetic and free (no API key, no flakiness), and lets a
reviewer run the entire product offline. It is clearly labelled and never presented as
real research. This is the spec's "mock the LLM" requirement made into a first-class,
demoable feature rather than test-only plumbing.

## Why FastAPI?
Async-capable, first-class Pydantic integration (request/response validation for free),
and automatic OpenAPI docs at `/docs`. It cleanly separates the frontend from the backend
behind a typed REST contract.

## Why a service + repository split?
Routers stay thin (validate → call service → shape response). Services hold business logic.
Repositories are the only code that touches the ORM query API. This keeps SQL out of routes,
makes the business logic unit-testable without HTTP, and localizes schema changes.

## Why a relational database?
Projects, personas, questions, responses, reports, themes and conversations have clear
parent/child relationships with referential integrity and cascade deletes. See
[database.md](database.md). Simple string lists are JSON columns to avoid over-normalizing.

## Why SQLite for dev, PostgreSQL for Docker?
SQLite gives a zero-setup local/test experience (a file, no server). PostgreSQL is the
production-grade target and is what Docker Compose runs. The same SQLAlchemy models and
Alembic migrations run on both (SQLite migrations use batch mode for ALTERs).

## Why fix the LangGraph memory with the database (audit bug B1)?
The original rebuilt the graph — and a fresh in-memory `MemorySaver` — on every call, so
`get_run_history()` could never recover a prior run. Rather than wire up a persistent
checkpointer, the **database is the source of truth** for durable, cross-run recovery: every
run's inputs, status, artifacts and errors are persisted rows. The graph is compiled once at
import and reused; a checkpointer would add complexity without adding durability the DB
doesn't already provide. This is honest about what recovery actually works.

## Why background tasks (not Celery/Redis)?
A research run takes many seconds to minutes — too long for a synchronous request. FastAPI
background tasks run it off-request and the DB status column reflects real progress. A full
queue + worker system (Celery/RQ + Redis) is the right answer *under real concurrency*, but
adding it now would be over-engineering for a single instance. The scale path is documented
in [architecture.md](architecture.md) and left as future work rather than faked.

## Why JWT auth?
Stateless bearer tokens fit a separate SPA + API cleanly (no server-side session store).
Passwords are bcrypt-hashed; tokens carry only the user id. Every research route is scoped
to the owner, and cross-user access returns 404 so existence isn't leaked.

## Why React + TypeScript + Vite (not Next.js)?
This is an authenticated SPA talking to a separate API — there is no SSR/SEO requirement that
would justify Next.js. Vite gives a faster, simpler build and dev server. TypeScript makes the
API contract explicit end-to-end (the frontend types mirror the backend schemas), catching
integration mistakes at compile time. React was chosen over adding it "for keywords" — it earns
its place through the stateful, multi-view UI (dashboard, polling detail view, chat).

## Why keep Streamlit?
It's retained as a small developer/demo UI that reuses the same service layer, so it can't
drift from production behaviour. It is not a second production frontend — the React SPA is the
product UI. Deleting it would remove a useful quick-testing path for no benefit.
