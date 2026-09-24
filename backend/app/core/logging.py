"""
Structured, leveled logging (spec §20, §41).

Logs are emitted as single-line JSON so they are greppable and machine-parseable
in production, and a ``request_id`` / ``run_id`` can be attached to correlate all
the log lines belonging to one HTTP request or one research run.

Secrets are never logged: the LLM service logs model names and durations, never
API keys or full prompts.
"""

import json
import logging
import sys
from contextvars import ContextVar

# Correlation IDs set per-request (middleware) and per-run (research service).
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
run_id_ctx: ContextVar[str | None] = ContextVar("run_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            payload["request_id"] = rid
        run_id = run_id_ctx.get()
        if run_id:
            payload["run_id"] = run_id
        # Structured extras attached via logger.info(..., extra={"extra": {...}})
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # Quiet noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, event: str, **fields) -> None:
    """Emit a structured event, e.g. log_event(log, INFO, "research.started", id=..)."""
    logger.log(level, event, extra={"extra": {"event": event, **fields}})
