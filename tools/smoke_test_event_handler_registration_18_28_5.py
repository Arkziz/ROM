#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sys
from pathlib import Path
from types import ModuleType
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import events

source=(ROOT/"main.py").read_text(encoding="utf-8-sig")
tree=ast.parse(source)
assert source.count("import events as seasonal_events")==1
assert source.count("seasonal_events.load_event_modules()")==1
assert source.count("seasonal_events.register_event_handlers(bot)")==1
assert source.index("seasonal_events.load_event_modules()") < source.index("seasonal_events.register_event_handlers(bot)")
assert source.index("seasonal_events.register_event_handlers(bot)") < source.index("register_crystal_shop_handlers(bot)")
assert events.EVENT_MODULES==()
events.reset_event_registry_for_tests()
assert events.load_event_modules()==()
registrations=[]
class Bot: pass
bot=Bot()
assert events.register_event_handlers(bot)==()

def make_event(key,enabled=True):
    module=ModuleType(f"events.{key}"); config=ModuleType(f"events.{key}.config")
    from datetime import datetime,timezone
    config.EVENT_KEY=key; config.ENABLED=enabled
    config.START_AT=datetime(2026,1,1,tzinfo=timezone.utc); config.END_AT=datetime(2027,1,1,tzinfo=timezone.utc)
    config.is_active=lambda now=None: enabled
    module.config=config; module.handlers=ModuleType(f"events.{key}.handlers")
    module.handlers.register=lambda value: registrations.append((key,value))
    return module

enabled=make_event("enabled"); disabled=make_event("disabled",False)
events.register_event("enabled",enabled); events.register_event("disabled",disabled)
assert events.register_event_handlers(bot)==("enabled",)
assert registrations==[("enabled",bot)]
events.reset_event_registry_for_tests()
print("EVENT_HANDLER_REGISTRATION_18_28_5_OK")
