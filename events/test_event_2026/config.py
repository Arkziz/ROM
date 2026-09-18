# -*- coding: utf-8 -*-
from datetime import datetime, timezone

EVENT_KEY = "test_event_2026"
TITLE = "Тестовий івент"
EVENT_NAME = "🧪 Тестовий івент"
DISPLAY_NAME = EVENT_NAME
EVENT_ICON = "🧪"
EVENT_SHORT_DESCRIPTION = "Тестовий наскрізний івент для перевірки encounter, drop, exchange та рейтингу."
ENABLED = False
ARCHIVE_VISIBLE = True
EVER_LAUNCHED = False
TIMEZONE_NAME = "Europe/Kyiv"
START_LOCAL = None
END_LOCAL = None
# Valid aware placeholders keep the foundation contract import-safe. Runtime is
# disabled until explicit Kyiv-local dates replace these sentinels.
START_AT = datetime(2099, 1, 1, tzinfo=timezone.utc)
END_AT = datetime(2099, 1, 2, tzinfo=timezone.utc)
DATE_POLICY = "PENDING_KYIV_ACTIVATION"



def is_active(now=None):
    if not ENABLED:
        return False
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return START_AT <= current.astimezone(timezone.utc) < END_AT
