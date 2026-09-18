# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - supported Python versions provide zoneinfo
    ZoneInfo = None
    class ZoneInfoNotFoundError(Exception):
        pass

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
LOCAL_DATETIME_FORMAT = "%d.%m.%Y %H:%M"

# Для повторного запуску тестового івенту змінюйте лише ці два рядки.
START_LOCAL = "20.09.2026 00:17"
END_LOCAL = "20.09.2026 00:32"
START_LOCAL_TEXT = START_LOCAL
END_LOCAL_TEXT = END_LOCAL
DATE_POLICY = "EUROPE_KYIV_LOCAL_CANONICAL"


def _last_sunday(year, month):
    if month == 12:
        first_next = datetime(year + 1, 1, 1)
    else:
        first_next = datetime(year, month + 1, 1)
    last_day = first_next - timedelta(days=1)
    return last_day.day - ((last_day.weekday() - 6) % 7)


def _fallback_kyiv_timezone(local_value):
    """Windows fallback when the IANA tzdata package is unavailable."""
    year = local_value.year
    dst_start = datetime(year, 3, _last_sunday(year, 3), 3, 0)
    dst_end = datetime(year, 10, _last_sunday(year, 10), 4, 0)
    if dst_start <= local_value < dst_end:
        return timezone(timedelta(hours=3), name="Europe/Kyiv")
    return timezone(timedelta(hours=2), name="Europe/Kyiv")


def _parse_kyiv_local(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must use DD.MM.YYYY HH:MM")
    try:
        local_value = datetime.strptime(value.strip(), LOCAL_DATETIME_FORMAT)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use DD.MM.YYYY HH:MM") from exc

    if ZoneInfo is not None:
        try:
            return local_value.replace(tzinfo=ZoneInfo(TIMEZONE_NAME))
        except ZoneInfoNotFoundError:
            pass
    return local_value.replace(tzinfo=_fallback_kyiv_timezone(local_value))


START_LOCAL_AT = _parse_kyiv_local(START_LOCAL, "START_LOCAL")
END_LOCAL_AT = _parse_kyiv_local(END_LOCAL, "END_LOCAL")
START_AT = START_LOCAL_AT.astimezone(timezone.utc)
END_AT = END_LOCAL_AT.astimezone(timezone.utc)

if START_AT >= END_AT:
    raise ValueError("END_LOCAL must be later than START_LOCAL")


def is_active(now=None):
    if not ENABLED:
        return False
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return START_AT <= current.astimezone(timezone.utc) < END_AT
