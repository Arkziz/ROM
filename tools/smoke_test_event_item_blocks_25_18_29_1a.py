# -*- coding: utf-8 -*-
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from events.item_namespace import (
    EVENT_STATIC_ITEM_MIN, EVENT_STATIC_ITEM_MAX, EVENT_ITEM_BLOCK_SIZE,
    EVENT_ITEM_BLOCK_COUNT, EVENT_ITEM_BLOCKS, EventItemNamespaceError,
    block_bounds, validate_block_registry, get_event_item_block,
    get_event_item_blocks, validate_event_item_id, validate_event_item_definitions,
)

def fails(fn):
    try:
        fn()
    except EventItemNamespaceError:
        return
    raise AssertionError("expected EventItemNamespaceError")

assert EVENT_STATIC_ITEM_MIN == 4000
assert EVENT_STATIC_ITEM_MAX == 9999
assert EVENT_ITEM_BLOCK_SIZE == 25
assert EVENT_ITEM_BLOCK_COUNT == 240
assert EVENT_ITEM_BLOCKS == {}
assert block_bounds(0) == (4000, 4024)
assert block_bounds(1) == (4025, 4049)
assert block_bounds(239) == (9975, 9999)
fails(lambda: block_bounds(-1))
fails(lambda: block_bounds(240))

one = {"event_a": ((4000, 4024),)}
multi = {"event_a": ((4000, 4024), (4025, 4049))}
assert validate_block_registry(one) == one
assert validate_block_registry(multi) == multi
assert get_event_item_block("event_a", multi) == (4000, 4024)
assert get_event_item_blocks("event_a", multi) == ((4000, 4024), (4025, 4049))
assert validate_event_item_id("event_a", 4000, multi) == 4000
assert validate_event_item_id("event_a", 4049, multi) == 4049
fails(lambda: validate_event_item_id("event_a", 4050, multi))
fails(lambda: validate_block_registry({"a": ((4000, 4024),), "b": ((4000, 4024),)}))
fails(lambda: validate_block_registry({"a": ((4000, 4024), (4000, 4024))}))
fails(lambda: validate_block_registry({"a": ((4000, 4049),)}))
fails(lambda: validate_block_registry({"a": ((4001, 4025),)}))
items = (
    {"event_key": "event_a", "item_key": "currency", "id": 4000},
    {"event_key": "event_a", "item_key": "reward", "id": 4025},
)
# Keep the canonical one-argument item-definition API. Install the isolated
# registry fixture process-locally, validate both assigned blocks, then clean up.
EVENT_ITEM_BLOCKS.update(multi)
try:
    assert validate_event_item_definitions(items) == items
finally:
    EVENT_ITEM_BLOCKS.clear()
assert EVENT_ITEM_BLOCKS == {}
print("EVENT_ITEM_BLOCKS_25_18_29_1A_OK")
