"""Validated environment configuration and redacted secret values for ROM V2."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from rom_v2.runtime_paths import RuntimePaths


class ConfigurationError(ValueError):
    """Report invalid configuration using a stable machine-readable reason."""


@dataclass(frozen=True, slots=True)
class SecretValue:
    """Hold a secret while preventing accidental repr or string disclosure."""

    _value: str

    @classmethod
    def from_required(cls, value: str | None, key: str) -> "SecretValue":
        """Create a non-empty secret or reject the missing environment key."""
        if value is None or not value.strip():
            raise ConfigurationError(f"missing_required_secret:{key}")
        return cls(value.strip())

    def reveal(self) -> str:
        """Return the secret only at the external adapter boundary."""
        return self._value

    def __repr__(self) -> str:
        """Render a constant redacted representation for logs and diagnostics."""
        return "SecretValue(<redacted>)"

    def __str__(self) -> str:
        """Render a constant redacted string instead of the protected value."""
        return "<redacted>"


@dataclass(frozen=True, slots=True)
class V2Settings:
    """Hold validated V2 settings loaded once by the composition root."""

    application_name: str
    environment: str
    log_level: str
    bot_token: SecretValue
    runtime_paths: RuntimePaths

    @classmethod
    def from_environment(
        cls,
        project_root: Path,
        environment: Mapping[str, str] | None = None,
    ) -> "V2Settings":
        """Load and validate settings without reading a local dotenv file."""
        values = os.environ if environment is None else environment
        application_name = values.get("ROM_V2_APPLICATION_NAME", "rom_v2").strip()
        runtime_environment = values.get("ROM_V2_ENVIRONMENT", "development").strip().lower()
        log_level = values.get("ROM_V2_LOG_LEVEL", "INFO").strip().upper()
        if not application_name:
            raise ConfigurationError("invalid_application_name")
        if runtime_environment not in {"development", "test", "production"}:
            raise ConfigurationError("invalid_environment")
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError("invalid_log_level")
        runtime_paths = RuntimePaths.from_project_root(project_root)
        runtime_paths.validate()
        return cls(
            application_name=application_name,
            environment=runtime_environment,
            log_level=log_level,
            bot_token=SecretValue.from_required(values.get("ROM_V2_BOT_TOKEN"), "ROM_V2_BOT_TOKEN"),
            runtime_paths=runtime_paths,
        )

    def safe_summary(self) -> dict[str, str]:
        """Return diagnostics that contain no secret value or secret metadata."""
        return {
            "application_name": self.application_name,
            "environment": self.environment,
            "log_level": self.log_level,
            "runtime_root": self.runtime_paths.root.as_posix(),
        }
