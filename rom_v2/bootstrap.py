"""Authoritative bootstrap factory for the isolated V2 skeleton."""
from __future__ import annotations

from rom_v2.config import V2Config
from rom_v2.container import V2Container
from rom_v2.lifecycle import V2Lifecycle


def build_lifecycle(config: V2Config | None = None) -> V2Lifecycle:
    """Build a lifecycle with explicit dependencies and gameplay disabled."""
    effective_config = config if config is not None else V2Config()
    return V2Lifecycle(container=V2Container(config=effective_config))
