# -*- coding: utf-8 -*-
from datetime import datetime, timezone

EVENT_KEY = "test_event_2026"
TITLE = "Тестовий івент"
EVENT_NAME = "🧪 Тестовий івент"
DISPLAY_NAME = EVENT_NAME
EVENT_ICON = "🧪"
EVENT_SHORT_DESCRIPTION = "Тестовий наскрізний івент для перевірки encounter, drop, exchange та рейтингу."
ENABLED = True
ARCHIVE_VISIBLE = True
EVER_LAUNCHED = False
TIMEZONE_NAME = "Europe/Kyiv"
START_LOCAL = "19.09.2026 00:15"
START_LOCAL_TEXT = START_LOCAL
END_LOCAL = "19.09.2026 00:30"
END_LOCAL_TEXT = END_LOCAL
# Valid aware placeholders keep the foundation contract import-safe. Runtime is
# disabled until explicit Kyiv-local dates replace these sentinels.
START_AT = datetime(2026, 9, 18, 21, 15, tzinfo=timezone.utc)
END_AT = datetime(2026, 9, 18, 21, 30, tzinfo=timezone.utc)
DATE_POLICY = "PENDING_KYIV_ACTIVATION"



def is_active(now=None):
    if not ENABLED:
        return False
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return START_AT <= current.astimezone(timezone.utc) < END_AT
