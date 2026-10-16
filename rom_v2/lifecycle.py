"""Startup and shutdown lifecycle for the isolated V2 skeleton."""
from __future__ import annotations

from dataclasses import dataclass

from rom_v2.container import V2Container


@dataclass(slots=True)
class V2Lifecycle:
    """Track bootstrap lifecycle without starting Telegram, DB, jobs, or gameplay."""

    container: V2Container
    started: bool = False

    def start(self) -> None:
        """Validate configuration and mark the isolated skeleton as started."""
        self.container.config.validate()
        self.started = True

    def stop(self) -> None:
        """Return the isolated skeleton to its stopped state."""
        self.started = False
