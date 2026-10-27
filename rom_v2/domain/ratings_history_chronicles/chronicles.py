"""Chronicle retention and newest-first pagination contract."""
from __future__ import annotations

from .models import ChronicleEvent, Page

CHRONICLE_RETENTION_LIMIT = 100
CHRONICLE_PAGE_SIZE = 10


def retain_chronicles(events: tuple[ChronicleEvent, ...], owner_id: int) -> tuple[ChronicleEvent, ...]:
    """Keep the newest 100 owner events with deterministic event_id tie ordering."""
    selected = [event for event in events if event.owner_id == owner_id]
    if len({event.event_id for event in selected}) != len(selected):
        raise ValueError("duplicate_chronicle_event_id")
    selected.sort(key=lambda event: (-int(event.occurred_at.timestamp() * 1_000_000), event.event_id))
    return tuple(selected[:CHRONICLE_RETENTION_LIMIT])


def chronicle_page(events: tuple[ChronicleEvent, ...], owner_id: int, page: int) -> Page:
    if page < 1:
        raise ValueError("page_must_be_positive")
    retained = retain_chronicles(events, owner_id)
    total = len(retained)
    pages = max(1, (total + CHRONICLE_PAGE_SIZE - 1) // CHRONICLE_PAGE_SIZE)
    start = (page - 1) * CHRONICLE_PAGE_SIZE
    items = retained[start:start + CHRONICLE_PAGE_SIZE] if page <= pages else ()
    return Page(items, page, CHRONICLE_PAGE_SIZE, total, pages, page > 1 and page <= pages, page < pages)
