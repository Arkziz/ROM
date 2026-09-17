#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import events
import events._template as template

def module(key, enabled=True):
    value=ModuleType(f"events.{key}"); config=ModuleType(f"events.{key}.config")
    config.EVENT_KEY=key; config.ENABLED=enabled
    config.START_AT=datetime(2026,1,1,tzinfo=timezone.utc); config.END_AT=datetime(2027,1,1,tzinfo=timezone.utc)
    config.is_active=lambda now=None: bool(config.ENABLED and config.START_AT <= (now or datetime.now(timezone.utc)) < config.END_AT)
    value.config=config; return value

assert template.get_mob_candidates({})==()
assert template.get_boss_candidates({})==()
assert template.get_drop_rules({})==()
assert template.get_items()==()
assert template.handlers.register(object()) is None
assert "_template" not in events.EVENT_REGISTRY

events.reset_event_registry_for_tests(); active=module("active"); disabled=module("disabled",False)
active.get_mob_candidates=lambda context: ({"event_key":"active","mob_key":"mob"},)
active.get_boss_candidates=lambda context: ({"event_key":"active","boss_key":"boss"},)
active.get_drop_rules=lambda context: ({"rule_id":"event:active:currency"},)
active.get_items=lambda: ({"item_key":"currency"},)
active.handlers=ModuleType("events.active.handlers"); registrations=[]; active.handlers.register=lambda bot: registrations.append(bot)
disabled.get_items=lambda: ({"item_key":"disabled_item"},)
disabled.handlers=ModuleType("events.disabled.handlers"); disabled.handlers.register=lambda bot: registrations.append("disabled")
events.register_event("active",active); events.register_event("disabled",disabled)
now=datetime(2026,6,1,tzinfo=timezone.utc)
assert events.collect_event_mob_candidates({},now)==({"event_key":"active","mob_key":"mob"},)
assert events.collect_event_boss_candidates({},now)==({"event_key":"active","boss_key":"boss"},)
assert events.collect_event_drop_rules({},now)==({"rule_id":"event:active:currency"},)
assert events.collect_registered_event_items()==({"item_key":"currency"},{"item_key":"disabled_item"})
bot=object(); assert events.register_event_handlers(bot)==("active",) and registrations==[bot]
active.get_mob_candidates=lambda context: []
try: events.collect_event_mob_candidates({},now)
except events.EventRegistryError as exc: assert "must return tuple" in str(exc)
else: raise AssertionError("list result accepted")
print("EVENT_CONTENT_CONTRACTS_18_28_3_OK")
