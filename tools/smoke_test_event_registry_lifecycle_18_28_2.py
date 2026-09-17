#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import ModuleType
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import events

def event(key,start,end,enabled=True):
    module=ModuleType(f"events.{key}"); config=ModuleType(f"events.{key}.config")
    config.EVENT_KEY=key; config.ENABLED=enabled; config.START_AT=start; config.END_AT=end
    def active(now=None):
        value=now or datetime.now(timezone.utc)
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("now must be timezone-aware")
        value=value.astimezone(timezone.utc)
        return bool(config.ENABLED and config.START_AT <= value < config.END_AT)
    config.is_active=active; module.config=config; return module

def error(action,text):
    try: action()
    except events.EventRegistryError as exc: assert text in str(exc),(text,exc)
    else: raise AssertionError(text)

events.reset_event_registry_for_tests()
assert events.EVENT_MODULES==() and events.get_registered_events()==()
start=datetime(2026,10,20,tzinfo=timezone.utc); end=datetime(2026,11,5,tzinfo=timezone.utc)
a=event("season_a",start,end); b=event("season_b",start,end,False)
events.register_event("season_a",a); events.register_event("season_b",b)
assert events.get_registered_events()==(a,b); assert events.get_enabled_events()==(a,)
assert events.get_active_events(start-timedelta(microseconds=1))==()
assert events.get_active_events(start)==(a,)
assert events.get_active_events(end-timedelta(microseconds=1))==(a,)
assert events.get_active_events(end)==()
assert events.get_active_events(start.astimezone(timezone(timedelta(hours=3))))==(a,)
error(lambda:events.register_event("season_a",a),"duplicate EVENT_KEY")
error(lambda:events.register_event("x",event("y",start,end)),"registry key must equal")
error(lambda:events.register_event("naive",event("naive",start.replace(tzinfo=None),end)),"timezone-aware")
error(lambda:events.register_event("reverse",event("reverse",end,start)),"earlier")
error(lambda:events.load_event_modules(("events._template",)),"must never be loaded")
error(lambda:events.load_event_modules(("outside.package",)),"inside events package")
error(lambda:events.load_event_modules(("events.a","events.a")),"unique")
error(lambda:events.get_active_events(datetime(2026,10,20)),"timezone-aware")
import events._template as template
assert template.config.ENABLED is False and "_template" not in events.EVENT_REGISTRY
assert template.config.is_active(datetime(2099,1,1,tzinfo=timezone.utc)) is False
print("EVENT_REGISTRY_LIFECYCLE_18_28_2_OK")
