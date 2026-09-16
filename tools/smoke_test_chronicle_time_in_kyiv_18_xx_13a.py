# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handlers.world_chronicles import _format_world_chronicle_time

assert _format_world_chronicle_time("2026-09-16T20:35:00+00:00") == "16.09.2026 23:35"
assert _format_world_chronicle_time("2026-09-16T20:35:00Z") == "16.09.2026 23:35"
assert _format_world_chronicle_time("2026-01-16T20:35:00+00:00") == "16.01.2026 22:35"
assert _format_world_chronicle_time("2026-09-16T20:35:00") == "16.09.2026 23:35"

import handlers.world_chronicles as chronicles
original_zoneinfo = chronicles.ZoneInfo
chronicles.ZoneInfo = lambda key: (_ for _ in ()).throw(chronicles.ZoneInfoNotFoundError(key))
try:
    assert chronicles._format_world_chronicle_time("2026-09-16T20:35:00+00:00") == "16.09.2026 23:35"
    assert chronicles._format_world_chronicle_time("2026-01-16T20:35:00+00:00") == "16.01.2026 22:35"
finally:
    chronicles.ZoneInfo = original_zoneinfo

assert _format_world_chronicle_time("") == "час невідомий"
assert "UTC" not in _format_world_chronicle_time("2026-09-16T20:35:00+00:00")

source = (PROJECT_ROOT / "handlers" / "world_chronicles.py").read_text(encoding="utf-8-sig")
ast.parse(source)
assert source.count('ZoneInfo("Europe/Kyiv")') == 1
assert 'strftime("%d.%m.%Y %H:%M UTC")' not in source

print("CHRONICLE_TIME_IN_KYIV_18_XX_13A_OK")
