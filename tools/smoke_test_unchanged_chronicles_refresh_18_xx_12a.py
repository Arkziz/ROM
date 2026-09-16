# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import handlers.world_chronicles as chronicles

SOURCE = (PROJECT_ROOT / "handlers" / "world_chronicles.py").read_text(encoding="utf-8-sig")
TREE = ast.parse(SOURCE)
assert SOURCE.count("def _is_message_not_modified_error(") == 1
assert SOURCE.count("def _show_world_chronicles(") == 1
assert "message is not modified" in SOURCE
assert "except Exception as error:" in SOURCE
assert "raise" in SOURCE

original_page_reader = chronicles.get_world_chronicle_page
chronicles.get_world_chronicle_page = lambda page, page_size: {
    "items": [],
    "page": 0,
    "has_previous": False,
    "has_next": False,
}

class UnchangedBot:
    def edit_message_text(self, *args, **kwargs):
        raise RuntimeError(
            "A request to the Telegram API was unsuccessful. Error code: 400. "
            "Description: Bad Request: message is not modified: specified new message "
            "content and reply markup are exactly the same"
        )

class ChangedBot:
    def __init__(self):
        self.calls = 0
    def edit_message_text(self, *args, **kwargs):
        self.calls += 1

class OtherErrorBot:
    def edit_message_text(self, *args, **kwargs):
        raise RuntimeError("Bad Request: message to edit not found")

assert chronicles._show_world_chronicles(UnchangedBot(), 1, page=0, message_id=2) is False
changed = ChangedBot()
assert chronicles._show_world_chronicles(changed, 1, page=0, message_id=2) is True
assert changed.calls == 1

try:
    chronicles._show_world_chronicles(OtherErrorBot(), 1, page=0, message_id=2)
except RuntimeError as error:
    assert "message to edit not found" in str(error)
else:
    raise AssertionError("Unexpected Telegram errors must propagate")

chronicles.get_world_chronicle_page = original_page_reader
print("UNCHANGED_CHRONICLES_REFRESH_18_XX_12A_OK")
