# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timezone
EVENT_KEY="_template"
ENABLED=False
START_AT=datetime(2099,1,1,tzinfo=timezone.utc)
END_AT=datetime(2099,1,2,tzinfo=timezone.utc)
def is_active(now: datetime | None=None) -> bool:
    current=now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    current_utc=current.astimezone(timezone.utc)
    return bool(ENABLED and START_AT <= current_utc < END_AT)
