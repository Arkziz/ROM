"""Deterministic top-100 ratings with stable tie ordering and own position."""
from __future__ import annotations

from dataclasses import dataclass
from .models import Page, RatingCandidate, RatingEntry

RATING_TOP_LIMIT = 100
RATING_PAGE_SIZE = 20


@dataclass(frozen=True, slots=True)
class RatingView:
    page: Page
    own_entry: RatingEntry | None


def _rank(candidates: tuple[RatingCandidate, ...]) -> tuple[RatingEntry, ...]:
    """Sort score descending and use subject_id ascending as a stable tie-breaker."""
    seen = set()
    ordered = []
    for candidate in candidates:
        if candidate.subject_id in seen:
            raise ValueError(f"duplicate_rating_subject::{candidate.subject_id}")
        seen.add(candidate.subject_id)
        ordered.append(candidate)
    ordered.sort(key=lambda item: (-item.score, item.subject_id))
    return tuple(RatingEntry(index, item.subject_id, item.display_name, item.score) for index, item in enumerate(ordered, 1))


def build_rating_view(candidates: tuple[RatingCandidate, ...], page: int, own_subject_id: int | None = None) -> RatingView:
    if page < 1:
        raise ValueError("page_must_be_positive")
    ranked = _rank(candidates)
    own = next((item for item in ranked if item.subject_id == own_subject_id), None)
    visible = ranked[:RATING_TOP_LIMIT]
    total = len(visible)
    pages = max(1, (total + RATING_PAGE_SIZE - 1) // RATING_PAGE_SIZE)
    if page > pages:
        items = ()
    else:
        start = (page - 1) * RATING_PAGE_SIZE
        items = visible[start:start + RATING_PAGE_SIZE]
    return RatingView(Page(items, page, RATING_PAGE_SIZE, total, pages, page > 1 and page <= pages, page < pages), own)
