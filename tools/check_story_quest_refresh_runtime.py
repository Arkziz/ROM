#!/usr/bin/env python3
"""Runtime-shaped check for unchanged and changed story-journal refreshes."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telebot.apihelper import ApiTelegramException
from handlers.story_quests import _edit_story_journal_safely


class FakeBot:
    def __init__(self, error=None):
        self.error = error
        self.edits = 0

    def edit_message_text(self, *args, **kwargs):
        self.edits += 1
        if self.error is not None:
            raise self.error
        return True


def telegram_error(description):
    result = SimpleNamespace(status_code=400)
    payload = {"ok": False, "error_code": 400, "description": description}
    return ApiTelegramException("editMessageText", result, payload)


def main():
    changed = FakeBot()
    assert _edit_story_journal_safely(
        changed, chat_id=1, message_id=2, text="new", reply_markup=None
    ) is True
    assert changed.edits == 1

    unchanged = FakeBot(telegram_error(
        "Bad Request: message is not modified: specified new message content "
        "and reply markup are exactly the same as a current content and reply markup of the message"
    ))
    assert _edit_story_journal_safely(
        unchanged, chat_id=1, message_id=2, text="same", reply_markup=None
    ) is False

    unrelated = FakeBot(telegram_error("Bad Request: message to edit not found"))
    try:
        _edit_story_journal_safely(
            unrelated, chat_id=1, message_id=2, text="x", reply_markup=None
        )
    except ApiTelegramException:
        pass
    else:
        raise AssertionError("unrelated Telegram error was swallowed")
    print("[PASS] unchanged story quest refresh runtime guard")


if __name__ == "__main__":
    main()
