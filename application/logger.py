"""Centralized structured logging configuration for the Application Layer."""

from __future__ import annotations

import contextvars
import json
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# Context variables for end-to-end request/session tracing
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="-")

DEFAULT_LOG_DIR = Path(__file__).resolve().parent / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "app.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

_SENSITIVE_KEY_FRAGMENTS = ("api_key", "apikey", "token", "secret", "password", "passwd", "auth")


class ContextFilter(logging.Filter):
    """Inject request_id and session_id from contextvars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.session_id = session_id_var.get()
        return True


def _resolve_log_level(log_level: str | None = None) -> int:
    """Resolve log level string to a standard logging level constant."""
    raw = (log_level or os.getenv("LOG_LEVEL") or "INFO").strip().upper()
    level = getattr(logging, raw, None)
    if not isinstance(level, int):
        return logging.INFO
    return level


def setup_logging(
    log_level: str | None = None,
    log_file: Path | None = None,
) -> logging.Logger:
    """Configure root logger with console and rotating file handlers (idempotent)."""
    level = _resolve_log_level(log_level)
    target_file = Path(log_file) if log_file else DEFAULT_LOG_FILE
    target_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicating handlers if setup_logging is called multiple times
    existing_names = {getattr(h, "name", None) for h in root_logger.handlers}
    context_filter = ContextFilter()

    if "app_console" not in existing_names:
        console_handler = logging.StreamHandler()
        console_handler.name = "app_console"
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | req=%(request_id)s | sess=%(session_id)s | %(name)s:%(funcName)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)

    if "app_rotating_file" not in existing_names:
        file_handler = RotatingFileHandler(
            target_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.name = "app_rotating_file"
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | req=%(request_id)s | sess=%(session_id)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)

    # Ensure existing managed handlers reflect updated level
    for handler in root_logger.handlers:
        if getattr(handler, "name", None) in ("app_console", "app_rotating_file"):
            handler.setLevel(level)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, ensuring logging is initialized."""
    if not any(
        getattr(h, "name", None) in ("app_console", "app_rotating_file")
        for h in logging.getLogger().handlers
    ):
        setup_logging()
    return logging.getLogger(name)


def generate_id(prefix: str = "") -> str:
    """Generate a short unique identifier for request or session tracing."""
    short = uuid.uuid4().hex[:12]
    return f"{prefix}{short}" if prefix else short


def set_request_context(
    request_id: str | None = None,
    session_id: str | None = None,
) -> tuple[contextvars.Token[str], contextvars.Token[str]]:
    """Bind request_id and session_id to the current execution context."""
    req_token = request_id_var.set(request_id or generate_id())
    sess_token = session_id_var.set(session_id or "-")
    return req_token, sess_token


def reset_request_context(
    tokens: tuple[contextvars.Token[str], contextvars.Token[str]],
) -> None:
    """Restore previous request_id and session_id context."""
    req_token, sess_token = tokens
    request_id_var.reset(req_token)
    session_id_var.reset(sess_token)


def truncate_payload(payload: Any, max_len: int = 500) -> str:
    """Serialize and truncate large payloads/DataFrames/JSON blobs for safe logging."""
    if payload is None:
        return "None"
    try:
        if isinstance(payload, (dict, list, tuple)):
            text = json.dumps(payload, default=str, ensure_ascii=False)
        else:
            text = str(payload)
    except Exception:
        text = repr(payload)

    text = text.replace("\n", " ").strip()
    if len(text) > max_len:
        return f"{text[:max_len]}... [truncated, total={len(text)} chars]"
    return text


def sanitize_args(args: dict[str, Any] | None, max_len: int = 500) -> str:
    """Redact sensitive keys from argument dicts and truncate for logging."""
    if not args:
        return "{}"
    sanitized: dict[str, Any] = {}
    for k, v in args.items():
        key_lower = str(k).lower()
        if any(frag in key_lower for frag in _SENSITIVE_KEY_FRAGMENTS):
            sanitized[k] = "***REDACTED***"
        else:
            sanitized[k] = v
    return truncate_payload(sanitized, max_len=max_len)
