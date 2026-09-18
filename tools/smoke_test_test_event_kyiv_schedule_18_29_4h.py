# -*- coding: utf-8 -*-
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from events.test_event_2026 import config
assert config.ENABLED is True
assert config.TIMEZONE_NAME=="Europe/Kyiv"
assert config.START_LOCAL=="19.09.2026 00:15"
assert config.END_LOCAL=="19.09.2026 00:30"
assert config.START_LOCAL_TEXT==config.START_LOCAL
assert config.END_LOCAL_TEXT==config.END_LOCAL
assert config.START_AT==datetime(2026,9,18,21,15,tzinfo=timezone.utc)
assert config.END_AT==datetime(2026,9,18,21,30,tzinfo=timezone.utc)
assert not config.is_active(datetime(2026,9,18,21,14,59,tzinfo=timezone.utc))
assert config.is_active(datetime(2026,9,18,21,15,0,tzinfo=timezone.utc))
assert config.is_active(datetime(2026,9,18,21,29,59,tzinfo=timezone.utc))
assert not config.is_active(datetime(2026,9,18,21,30,0,tzinfo=timezone.utc))
print("TEST_EVENT_KYIV_SCHEDULE_18_29_4H_OK")
