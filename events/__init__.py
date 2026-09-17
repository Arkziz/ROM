# -*- coding: utf-8 -*-
"""Registry and lifecycle policy for ROM seasonal events."""
from __future__ import annotations
import importlib
import sys
from datetime import datetime, timezone
from types import ModuleType
from typing import Iterable

EVENT_MODULES: tuple[str, ...] = ()
EVENT_REGISTRY: dict[str, ModuleType] = {}
_LOADED_EVENT_MODULES: set[str] = set()

class EventRegistryError(ValueError):
    pass

def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise EventRegistryError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise EventRegistryError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)

def validate_event_contract(key: str, module: ModuleType) -> dict:
    normalized=str(key or "").strip()
    if not normalized or normalized.startswith("_"):
        raise EventRegistryError("EVENT_KEY must be non-empty and must not start with underscore")
    config=getattr(module,"config",None)
    if config is None:
        raise EventRegistryError("event module must expose config")
    if str(getattr(config,"EVENT_KEY","") or "").strip()!=normalized:
        raise EventRegistryError("registry key must equal config.EVENT_KEY")
    if not isinstance(getattr(config,"ENABLED",None),bool):
        raise EventRegistryError("config.ENABLED must be bool")
    start=_utc(getattr(config,"START_AT",None),"START_AT")
    end=_utc(getattr(config,"END_AT",None),"END_AT")
    if start>=end:
        raise EventRegistryError("START_AT must be earlier than END_AT")
    if not callable(getattr(config,"is_active",None)):
        raise EventRegistryError("config.is_active must be callable")
    return {"event_key":normalized,"enabled":config.ENABLED,"start_at":start,"end_at":end}

def register_event(key: str, module: ModuleType) -> ModuleType:
    contract=validate_event_contract(key,module); key=contract["event_key"]
    if key in EVENT_REGISTRY:
        raise EventRegistryError(f"duplicate EVENT_KEY: {key}")
    EVENT_REGISTRY[key]=module
    return module

def load_event_modules(module_names: Iterable[str] | None=None) -> tuple[ModuleType,...]:
    selected=EVENT_MODULES if module_names is None else tuple(module_names)
    normalized=tuple(str(raw or "").strip() for raw in selected)
    if any(not name for name in normalized) or len(set(normalized)) != len(normalized):
        raise EventRegistryError("EVENT_MODULES must contain unique non-empty module names")
    loaded=[]; seen=set()
    for name in normalized:
        if name=="events._template" or name.startswith("events._template."):
            raise EventRegistryError("events._template must never be loaded as an event")
        if not name.startswith("events."):
            raise EventRegistryError("event module must be inside events package")
        seen.add(name)
        if name not in _LOADED_EVENT_MODULES:
            importlib.import_module(name); _LOADED_EVENT_MODULES.add(name)
        loaded.append(sys.modules[name])
    return tuple(loaded)

def get_registered_events() -> tuple[ModuleType,...]:
    return tuple(EVENT_REGISTRY[key] for key in sorted(EVENT_REGISTRY))

def get_enabled_events() -> tuple[ModuleType,...]:
    return tuple(module for module in get_registered_events() if validate_event_contract(module.config.EVENT_KEY,module)["enabled"])

def get_active_events(now: datetime | None=None) -> tuple[ModuleType,...]:
    current=_utc(now or datetime.now(timezone.utc),"now")
    return tuple(module for module in get_enabled_events() if bool(module.config.is_active(now=current)))

def reset_event_registry_for_tests() -> None:
    EVENT_REGISTRY.clear(); _LOADED_EVENT_MODULES.clear()
