#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import events
from events import item_namespace as ns
readme=(ROOT/"events/README.md").read_text(encoding="utf-8-sig")
closure=(ROOT/"MD/STAGE_18_28_EVENT_ENGINE_FOUNDATION_CLOSURE.md").read_text(encoding="utf-8-sig")
continuation=(ROOT/"MD/STAGE_18_29_EVENT_PILOT_CONTINUATION.md").read_text(encoding="utf-8-sig")
for relative in ("events/__init__.py","events/item_namespace.py","systems/boss_system.py","systems/drop_system.py","systems/reward_system.py","main.py"):
 source=(ROOT/relative).read_text(encoding="utf-8-sig");ast.parse(source);compile(source,relative,"exec")
assert "Stage 18.28 foundation closure" in readme
assert "`CLOSED`" in closure and "4000..9999" in closure and "120 blocks" in closure
assert "event_normal -> boss -> elite -> normal" in closure
assert "Stage 18.29" in continuation and "4000..4049" in continuation
assert events.EVENT_MODULES==() and events.get_registered_events()==()
assert events.collect_event_mob_candidates({})==()
assert events.collect_event_boss_candidates({})==()
assert events.collect_event_drop_rules({})==()
assert events.collect_registered_event_items()==()
assert events.register_event_handlers(object())==()
assert ns.EVENT_STATIC_ITEM_MIN==4000 and ns.EVENT_STATIC_ITEM_MAX==9999
assert ns.EVENT_ITEM_BLOCK_SIZE == 25 and ns.EVENT_ITEM_BLOCK_COUNT == 240
assert ns.EVENT_ITEM_BLOCKS=={}
assert not hasattr(events,"select_event_boss_candidate")
print("EVENT_ENGINE_FOUNDATION_CLOSURE_18_28_9_OK")
