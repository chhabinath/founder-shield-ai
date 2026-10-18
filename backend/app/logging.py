"""Structured JSON logging with secret / sensitive-data redaction.

A redaction filter is applied to every log record before emission so that
secrets or PII never reach the logs. Detection is heuristic and treated as
imperfect; it is a safety net, not the privacy boundary (see Phase 03).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

_REDACTIONS: list[tuple[re.Pattern[str], str]] = [
    # OpenAI-style keys first (more specific than generic email/phone).
    (re.compile(r"sk-[A-Za-z0-9]{8,}"), "[REDACTED_KEY]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    # key=value / key: value where key looks sensitive.
    (
        re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token|authorization)\b(\s*[=:]\s*)\S+"),
        r"\1\2[REDACTED]",
    ),
    # Phone-like sequences (loose; redaction is a safety net).
    (re.compile(r"(?<!\w)\+?\d[\d\s().\-]{7,}\d(?!\w)"), "[REDACTED_PHONE]"),
]


def redact(text: str) -> str:
    """Redact known sensitive patterns from a string."""
    if not isinstance(text, str):
        text = str(text)
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


class RedactionFilter(logging.Filter):
    """Logging filter that redacts message and string args in place."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: (redact(v) if isinstance(v, str) else v)
                        for k, v in record.args.items()
                    }
                else:
                    record.args = tuple(
                        redact(a) if isinstance(a, str) else a for a in record.args
                    )
        except Exception:
            # Never let logging raise. Fail safe: keep the record.
            pass
        return True


class JsonFormatter(logging.Formatter):
    """Minimal structured JSON formatter."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            # Redact any text pulled from exception formatting.
            payload["exc"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging(level: str = "info") -> logging.Logger:
    """Configure the root application logger with redaction + JSON output."""
    logger = logging.getLogger("foundershield")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactionFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
