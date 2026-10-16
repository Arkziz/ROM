"""Secret-safe structured JSON logging for ROM V2 diagnostics."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

SENSITIVE_KEY_PARTS = ("token", "secret", "password", "authorization", "cookie", "api_key", "private_key")
ALLOWED_ERROR_CATEGORIES = frozenset({"none", "validation", "business", "stale", "retryable", "consistency", "unexpected"})


def _redact(value: Any, key: str = "") -> Any:
    """Recursively redact sensitive fields and unsupported payload objects."""
    normalized = key.lower()
    if any(part in normalized for part in SENSITIVE_KEY_PARTS):
        return "<redacted>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(item_key): _redact(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return "<unsupported>"


@dataclass(frozen=True, slots=True)
class LogContext:
    """Carry stable diagnostic identifiers across one domain operation."""

    correlation_id: str
    operation: str

    def validate(self) -> None:
        """Reject empty or presentation-shaped diagnostic identifiers."""
        if not self.correlation_id.strip():
            raise ValueError("missing_correlation_id")
        if not self.operation.strip() or any(character.isspace() for character in self.operation):
            raise ValueError("invalid_operation_key")


class JsonLogFormatter(logging.Formatter):
    """Serialize canonical log records as one compact JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render required fields while redacting structured diagnostic details."""
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "timestamp_utc": timestamp,
            "level": record.levelname.lower(),
            "event": getattr(record, "event_key", "runtime.message"),
            "correlation_id": getattr(record, "correlation_id", "system"),
            "operation": getattr(record, "operation", "runtime"),
            "error_category": getattr(record, "error_category", "none"),
            "details": _redact(getattr(record, "details", {})),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def configure_structured_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create one non-propagating logger with exactly one JSON stream handler."""
    logger = logging.getLogger(name)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    level: int,
    event_key: str,
    context: LogContext,
    *,
    error_category: str = "none",
    details: Mapping[str, Any] | None = None,
) -> None:
    """Emit one canonical diagnostic event without accepting free-form payload text."""
    context.validate()
    if not event_key.strip() or any(character.isspace() for character in event_key):
        raise ValueError("invalid_event_key")
    if error_category not in ALLOWED_ERROR_CATEGORIES:
        raise ValueError("invalid_error_category")
    logger.log(
        level,
        event_key,
        extra={
            "event_key": event_key,
            "correlation_id": context.correlation_id,
            "operation": context.operation,
            "error_category": error_category,
            "details": dict(details or {}),
        },
    )
