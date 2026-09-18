# -*- coding: utf-8 -*-
"""Canonical never-reuse namespace for static seasonal event item types."""
from __future__ import annotations

from collections.abc import Mapping

EVENT_STATIC_ITEM_MIN = 4000
EVENT_STATIC_ITEM_MAX = 9999
EVENT_ITEM_BLOCK_SIZE = 25
EVENT_ITEM_BLOCK_COUNT = 240

# Permanent owner reservations. Add one entry only when a production EVENT_KEY is approved.
EVENT_ITEM_BLOCKS = {"test_event_2026": ((4000, 4024),)}

# Stage 18.29.1a policy: blocks contain 25 IDs. One EVENT_KEY starts with one
# permanent block and may later receive another explicit free block. Assigned
# blocks are never reused by another event.

class EventItemNamespaceError(ValueError):
    pass

def block_bounds(block_index: int) -> tuple[int, int]:
    index=int(block_index)
    if index < 0 or index >= EVENT_ITEM_BLOCK_COUNT:
        raise EventItemNamespaceError("event item block index is out of range")
    start=EVENT_STATIC_ITEM_MIN + index * EVENT_ITEM_BLOCK_SIZE
    return start, start + EVENT_ITEM_BLOCK_SIZE - 1

def _normalize_event_key(event_key):
    key = str(event_key or "").strip()
    if not key:
        raise EventItemNamespaceError("EVENT_KEY must be non-empty")
    return key


def _normalize_block(block):
    if not isinstance(block, tuple) or len(block) != 2:
        raise EventItemNamespaceError("each reserved block must be a (start, end) tuple")
    start, end = block
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)):
        raise EventItemNamespaceError("block bounds must be integers")
    if start < EVENT_STATIC_ITEM_MIN or end > EVENT_STATIC_ITEM_MAX:
        raise EventItemNamespaceError("reserved block is outside event namespace")
    if end - start + 1 != EVENT_ITEM_BLOCK_SIZE:
        raise EventItemNamespaceError("reserved block must contain exactly 25 IDs")
    if (start - EVENT_STATIC_ITEM_MIN) % EVENT_ITEM_BLOCK_SIZE != 0:
        raise EventItemNamespaceError("reserved block is not aligned to event namespace")
    return start, end


def validate_block_registry(registry=None):
    """Validate permanent one-or-more block ownership per EVENT_KEY."""
    source = EVENT_ITEM_BLOCKS if registry is None else registry
    if not isinstance(source, Mapping):
        raise EventItemNamespaceError("block registry must be a mapping")
    normalized = {}
    owners = {}
    for raw_key, raw_blocks in source.items():
        event_key = _normalize_event_key(raw_key)
        if not isinstance(raw_blocks, tuple) or not raw_blocks:
            raise EventItemNamespaceError("each EVENT_KEY must own a non-empty tuple of blocks")
        event_blocks = []
        local_seen = set()
        for raw_block in raw_blocks:
            block = _normalize_block(raw_block)
            if block in local_seen:
                raise EventItemNamespaceError("duplicate block inside one EVENT_KEY")
            local_seen.add(block)
            if block in owners and owners[block] != event_key:
                raise EventItemNamespaceError("one block cannot belong to multiple EVENT_KEY values")
            owners[block] = event_key
            event_blocks.append(block)
        normalized[event_key] = tuple(event_blocks)
    return normalized


def get_event_item_blocks(event_key, registry=None):
    key = _normalize_event_key(event_key)
    validated = validate_block_registry(registry)
    if key not in validated:
        raise EventItemNamespaceError(f"EVENT_KEY has no reserved item block: {key}")
    return validated[key]


def get_event_item_block(event_key, registry=None):
    """Compatibility helper returning the first assigned block."""
    return get_event_item_blocks(event_key, registry)[0]


def validate_event_item_id(event_key, item_id, registry=None):
    if isinstance(item_id, bool) or not isinstance(item_id, int):
        raise EventItemNamespaceError("item_id must be an integer")
    blocks = get_event_item_blocks(event_key, registry)
    if not any(start <= item_id <= end for start, end in blocks):
        raise EventItemNamespaceError("item_id is outside all blocks assigned to EVENT_KEY")
    return item_id


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
