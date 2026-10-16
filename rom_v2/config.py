"""Minimal non-secret V2 bootstrap configuration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class V2Config:
    """Hold only safe bootstrap settings before validated secret loading exists."""

    application_name: str = "rom_v2"
    mode: str = "bootstrap"
    gameplay_enabled: bool = False

    def validate(self) -> None:
        """Reject any configuration that could activate gameplay in the skeleton."""
        if self.gameplay_enabled:
            raise ValueError("gameplay_enabled_must_remain_false_in_stage_21_3_1")
