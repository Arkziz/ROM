#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from events import item_namespace as ns

def failure(action,text):
    try: action()
    except ns.EventItemNamespaceError as exc: assert text in str(exc),(text,exc)
    else: raise AssertionError(text)

assert ns.EVENT_STATIC_ITEM_MIN==4000
assert ns.EVENT_STATIC_ITEM_MAX==9999
assert ns.EVENT_ITEM_BLOCK_SIZE==50
assert ns.EVENT_ITEM_BLOCK_COUNT==120
assert ns.block_bounds(0)==(4000,4049)
assert ns.block_bounds(119)==(9950,9999)
assert ns.validate_block_registry()=={}
failure(lambda:ns.block_bounds(-1),"out of range")
failure(lambda:ns.block_bounds(120),"out of range")
failure(lambda:ns.validate_block_registry({"a":(4000,4048)}),"exactly 50")
failure(lambda:ns.validate_block_registry({"a":(4001,4050)}),"not aligned")
failure(lambda:ns.validate_block_registry({"a":(3950,3999)}),"outside")
failure(lambda:ns.validate_block_registry({"a":(4000,4049),"b":(4000,4049)}),"overlap")
ns.EVENT_ITEM_BLOCKS.update({"pilot":(4000,4049),"second":(4050,4099)})
assert ns.validate_event_item_id("pilot",4000)==4000
assert ns.validate_event_item_id("pilot",4049)==4049
failure(lambda:ns.validate_event_item_id("pilot",4050),"outside block")
failure(lambda:ns.validate_event_item_id("missing",4000),"no reserved")
valid=({"event_key":"pilot","item_key":"currency","id":4000},{"event_key":"pilot","item_key":"reward","id":4001})
assert ns.validate_event_item_definitions(valid)==valid
failure(lambda:ns.validate_event_item_definitions((valid[0],dict(valid[0]))),"duplicate event item ID")
failure(lambda:ns.validate_event_item_definitions((valid[0],{"event_key":"pilot","item_key":"currency","id":4001})),"duplicate event item_key")
ns.EVENT_ITEM_BLOCKS.clear()
print("EVENT_ITEM_NAMESPACE_18_28_4A_OK")
