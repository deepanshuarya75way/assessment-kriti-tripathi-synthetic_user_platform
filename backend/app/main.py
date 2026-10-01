"""
FastAPI application entry point (spec §24).

Wires together: structured logging, a request-id middleware for tracing, CORS
for the SPA, the uniform error envelope, and the versioned API router. In
development (SQLite) tables are auto-created on startup so a reviewer can run the
API with zero migration steps; production uses Alembic migrations.
"""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, request_id_ctx

configure_logging(settings.log_level)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: "FastAPI"):
    # In dev/test with SQLite, create tables directly for a zero-setup start.
    # Production runs `alembic upgrade head` instead (see docker-compose / README).
    if settings.is_sqlite:
        import app.models  # noqa: F401 - registers all tables on Base
        from app.db.base import Base, engine

        Base.metadata.create_all(bind=engine)
    log.info("Startup complete (env=%s, llm=%s)", settings.environment, settings.llm_provider)
    yield


DESCRIPTION = """
Backend API for the **Synthetic User Research Platform** — generate AI-simulated
personas, run them through a survey, extract insights, chat with a persona, and
export a PDF report.

> Personas and responses are AI-generated (synthetic). Treat results as
> exploratory, not statistically representative.
"""

app = FastAPI(
    title=settings.app_title,
    version=__version__,
    description=DESCRIPTION,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
    token = request_id_ctx.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"name": settings.app_title, "version": __version__, "docs": "/docs"}
