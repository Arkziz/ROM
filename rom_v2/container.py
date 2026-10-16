"""Dependency container for the isolated V2 skeleton."""
from __future__ import annotations

from dataclasses import dataclass

from rom_v2.config import V2Config


@dataclass(frozen=True, slots=True)
class V2Container:
    """Own the minimal dependencies required by the bootstrap lifecycle."""

    config: V2Config
