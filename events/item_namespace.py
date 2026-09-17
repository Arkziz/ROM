# -*- coding: utf-8 -*-
"""Canonical never-reuse namespace for static seasonal event item types."""
from __future__ import annotations

EVENT_STATIC_ITEM_MIN = 4000
EVENT_STATIC_ITEM_MAX = 9999
EVENT_ITEM_BLOCK_SIZE = 50
EVENT_ITEM_BLOCK_COUNT = 120

# Permanent owner reservations. Add one entry only when a production EVENT_KEY is approved.
EVENT_ITEM_BLOCKS: dict[str, tuple[int, int]] = {}

class EventItemNamespaceError(ValueError):
    pass

def block_bounds(block_index: int) -> tuple[int, int]:
    index=int(block_index)
    if index < 0 or index >= EVENT_ITEM_BLOCK_COUNT:
        raise EventItemNamespaceError("event item block index is out of range")
    start=EVENT_STATIC_ITEM_MIN + index * EVENT_ITEM_BLOCK_SIZE
    return start, start + EVENT_ITEM_BLOCK_SIZE - 1

def validate_block_registry(blocks=None) -> dict[str, tuple[int, int]]:
    selected=EVENT_ITEM_BLOCKS if blocks is None else blocks
    if not isinstance(selected,dict):
        raise EventItemNamespaceError("EVENT_ITEM_BLOCKS must be dict")
    normalized={}; occupied=set()
    for raw_key,raw_bounds in selected.items():
        key=str(raw_key or "").strip()
        if not key or key.startswith("_"):
            raise EventItemNamespaceError("reserved EVENT_KEY must be non-empty and public")
        if not isinstance(raw_bounds,tuple) or len(raw_bounds)!=2:
            raise EventItemNamespaceError("event block bounds must be a two-value tuple")
        start,end=(int(raw_bounds[0]),int(raw_bounds[1]))
        if end-start+1 != EVENT_ITEM_BLOCK_SIZE:
            raise EventItemNamespaceError("event block must contain exactly 50 IDs")
        if start < EVENT_STATIC_ITEM_MIN or end > EVENT_STATIC_ITEM_MAX:
            raise EventItemNamespaceError("event block is outside static namespace")
        if (start-EVENT_STATIC_ITEM_MIN) % EVENT_ITEM_BLOCK_SIZE:
            raise EventItemNamespaceError("event block start is not aligned")
        ids=set(range(start,end+1))
        if occupied.intersection(ids):
            raise EventItemNamespaceError("event item blocks overlap")
        occupied.update(ids); normalized[key]=(start,end)
    return normalized

def get_event_item_block(event_key: str) -> tuple[int, int]:
    key=str(event_key or "").strip(); blocks=validate_block_registry()
    if key not in blocks:
        raise EventItemNamespaceError(f"EVENT_KEY has no reserved item block: {key}")
    return blocks[key]

def validate_event_item_id(event_key: str, item_id: int) -> int:
    value=int(item_id); start,end=get_event_item_block(event_key)
    if not start <= value <= end:
        raise EventItemNamespaceError(f"item ID {value} is outside block {start}..{end}")
    return value

def validate_event_item_definitions(definitions: tuple) -> tuple[dict,...]:
    if not isinstance(definitions,tuple):
        raise EventItemNamespaceError("event item definitions must be tuple")
    seen_ids=set(); seen_keys=set(); validated=[]
    for raw in definitions:
        if not isinstance(raw,dict):
            raise EventItemNamespaceError("event item definition must be dict")
        item=dict(raw); event_key=str(item.get("event_key") or "").strip(); item_key=str(item.get("item_key") or "").strip()
        if not item_key:
            raise EventItemNamespaceError("event item_key must be non-empty")
        item_id=validate_event_item_id(event_key,item.get("id"))
        if item_id in seen_ids:
            raise EventItemNamespaceError(f"duplicate event item ID: {item_id}")
        semantic=(event_key,item_key)
        if semantic in seen_keys:
            raise EventItemNamespaceError(f"duplicate event item_key: {event_key}:{item_key}")
        seen_ids.add(item_id); seen_keys.add(semantic); validated.append(item)
    return tuple(validated)
