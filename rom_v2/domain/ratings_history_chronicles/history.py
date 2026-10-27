"""Read-only history paging for completed trade and result-bearing PvP records."""
from __future__ import annotations

from .models import HistoryRecord, Page

HISTORY_PAGE_SIZE = 10
HISTORY_LIMIT_PER_KIND = 100
ALLOWED_HISTORY_KINDS = frozenset({"trade_completed", "pvp_result"})


def history_page(records: tuple[HistoryRecord, ...], owner_id: int, kind: str, page: int) -> Page:
    if kind not in ALLOWED_HISTORY_KINDS:
        raise ValueError(f"unsupported_history_kind::{kind}")
    if page < 1:
        raise ValueError("page_must_be_positive")
    selected = [item for item in records if item.owner_id == owner_id and item.kind == kind]
    if len({item.record_id for item in selected}) != len(selected):
        raise ValueError("duplicate_history_record_id")
    selected.sort(key=lambda item: (-int(item.occurred_at.timestamp() * 1_000_000), item.record_id))
    retained = tuple(selected[:HISTORY_LIMIT_PER_KIND])
    total = len(retained)
    pages = max(1, (total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE)
    start = (page - 1) * HISTORY_PAGE_SIZE
    items = retained[start:start + HISTORY_PAGE_SIZE] if page <= pages else ()
    return Page(items, page, HISTORY_PAGE_SIZE, total, pages, page > 1 and page <= pages, page < pages)
