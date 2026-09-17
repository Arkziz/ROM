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


def _optional_tuple(module: ModuleType, attribute: str) -> tuple:
    value = getattr(module, attribute, ())
    if value is None:
        return ()
    if not isinstance(value, tuple):
        raise EventRegistryError(f"{module.__name__}.{attribute} must be tuple")
    return value


def collect_event_mob_candidates(context, now: datetime | None = None) -> tuple:
    candidates = []
    for event_module in get_active_events(now=now):
        provider = getattr(event_module, "get_mob_candidates", None)
        if provider is not None:
            if not callable(provider):
                raise EventRegistryError(f"{event_module.__name__}.get_mob_candidates must be callable")
            candidates.extend(_optional_tuple_result(event_module, "get_mob_candidates", provider(context)))
    return tuple(candidates)


def collect_event_boss_candidates(context, now: datetime | None = None) -> tuple:
    candidates = []
    for event_module in get_active_events(now=now):
        provider = getattr(event_module, "get_boss_candidates", None)
        if provider is not None:
            if not callable(provider):
                raise EventRegistryError(f"{event_module.__name__}.get_boss_candidates must be callable")
            candidates.extend(_optional_tuple_result(event_module, "get_boss_candidates", provider(context)))
    return tuple(candidates)


def collect_event_drop_rules(context, now: datetime | None = None) -> tuple:
    rules = []
    for event_module in get_active_events(now=now):
        provider = getattr(event_module, "get_drop_rules", None)
        if provider is not None:
            if not callable(provider):
                raise EventRegistryError(f"{event_module.__name__}.get_drop_rules must be callable")
            rules.extend(_optional_tuple_result(event_module, "get_drop_rules", provider(context)))
    return tuple(rules)


def collect_registered_event_items() -> tuple:
    items = []
    for event_module in get_registered_events():
        provider = getattr(event_module, "get_items", None)
        if provider is not None:
            if not callable(provider):
                raise EventRegistryError(f"{event_module.__name__}.get_items must be callable")
            items.extend(_optional_tuple_result(event_module, "get_items", provider()))
    return tuple(items)


def register_event_handlers(bot) -> tuple[str, ...]:
    registered = []
    for event_module in get_enabled_events():
        handler_module = getattr(event_module, "handlers", None)
        register = getattr(handler_module, "register", None) if handler_module is not None else None
        if register is None:
            continue
        if not callable(register):
            raise EventRegistryError(f"{event_module.__name__}.handlers.register must be callable")
        register(bot)
        registered.append(str(event_module.config.EVENT_KEY))
    return tuple(registered)


def _optional_tuple_result(module: ModuleType, provider_name: str, value) -> tuple:
    if value is None:
        return ()
    if not isinstance(value, tuple):
        raise EventRegistryError(f"{module.__name__}.{provider_name} must return tuple")
    return value


def get_validated_registered_event_items() -> tuple[dict, ...]:
    from .item_namespace import validate_event_item_definitions
    return validate_event_item_definitions(collect_registered_event_items())


def validate_event_mob_candidates(candidates: tuple) -> tuple[dict, ...]:
    if not isinstance(candidates, tuple):
        raise EventRegistryError("event mob candidates must be tuple")
    validated = []
    for raw in candidates:
        if not isinstance(raw, dict):
            raise EventRegistryError("event mob candidate must be dict")
        candidate = dict(raw)
        event_key = str(candidate.get("event_key") or "").strip()
        mob_key = str(candidate.get("mob_key") or "").strip()
        template = candidate.get("mob_template")
        weight = float(candidate.get("weight", 1.0))
        chance = float(candidate.get("chance_percent", 0.0))
        if not event_key or not mob_key:
            raise EventRegistryError("event mob candidate keys must be non-empty")
        if not isinstance(template, dict):
            raise EventRegistryError("event mob candidate mob_template must be dict")
        if weight <= 0:
            raise EventRegistryError("event mob candidate weight must be positive")
        if not 0.0 <= chance <= 100.0:
            raise EventRegistryError("event mob candidate chance_percent must be between 0 and 100")
        candidate.update({"event_key": event_key, "mob_key": mob_key, "weight": weight, "chance_percent": chance})
        validated.append(candidate)
    return tuple(validated)


def select_event_mob_candidate(candidates: tuple, rng=None, chance_percent=None):
    import random as _random
    validated = validate_event_mob_candidates(candidates)
    if not validated:
        return None
    roller = rng or _random
    chance = max(float(row["chance_percent"]) for row in validated) if chance_percent is None else float(chance_percent)
    chance = max(0.0, min(100.0, chance))
    if float(roller.random()) >= chance / 100.0:
        return None
    total = sum(float(row["weight"]) for row in validated)
    point = float(roller.random()) * total
    cumulative = 0.0
    for row in validated:
        cumulative += float(row["weight"])
        if point < cumulative:
            return row
    return validated[-1]


def validate_event_drop_rules(rules: tuple, mob: dict) -> tuple[dict, ...]:
    if not isinstance(rules, tuple):
        raise EventRegistryError("event drop rules must be tuple")
    if not isinstance(mob, dict):
        raise EventRegistryError("event drop mob must be dict")
    if not mob.get("is_event"):
        return ()
    event_key = str(mob.get("event_key") or "").strip()
    mob_key = str(mob.get("event_mob_key") or "").strip()
    validated=[]; seen=set()
    for raw in rules:
        if not isinstance(raw, dict):
            raise EventRegistryError("event drop rule must be dict")
        rule=dict(raw); rule_id=str(rule.get("rule_id") or "").strip()
        if not rule_id or rule_id in seen:
            raise EventRegistryError("event drop rule_id must be unique and non-empty")
        if str(rule.get("event_key") or "").strip()!=event_key:
            continue
        target=str(rule.get("mob_key") or "*").strip()
        if target not in ("*",mob_key):
            continue
        item_id=int(rule.get("item_id")); quantity=int(rule.get("quantity",1)); chance=float(rule.get("chance_percent",0.0))
        if quantity <= 0:
            raise EventRegistryError("event drop quantity must be positive")
        if not 0.0 <= chance <= 100.0:
            raise EventRegistryError("event drop chance_percent must be between 0 and 100")
        from .item_namespace import validate_event_item_id
        validate_event_item_id(event_key,item_id)
        rule.update({"rule_id":rule_id,"event_key":event_key,"mob_key":target,"item_id":item_id,"quantity":quantity,"chance_percent":chance})
        seen.add(rule_id); validated.append(rule)
    return tuple(validated)
