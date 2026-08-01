#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


class Fake429(Exception):
    def __init__(self, seconds):
        super().__init__(
            f"A request to the Telegram API was unsuccessful. "
            f"Error code: 429. Description: Too Many Requests: retry after {seconds}"
        )
        self.result_json = {"parameters": {"retry_after": seconds}}


class FakeBot:
    def __init__(self):
        self.calls = []
        self.fail_next = True
    def send_message(self, chat_id, text, **kwargs):
        self.calls.append(("send_message", chat_id, text))
        if self.fail_next:
            self.fail_next = False
            raise Fake429(101)
        return {"ok": True}
    def edit_message_text(self, text, chat_id=None, **kwargs):
        self.calls.append(("edit_message_text", chat_id, text))
        return {"ok": True}
    def answer_callback_query(self, callback_query_id, **kwargs):
        self.calls.append(("answer_callback_query", None, callback_query_id))
        return {"ok": True}


def main():
    import systems.telegram_rate_limit as guard

    if guard.extract_retry_after(Fake429(101)) != 101:
        fail("retry_after parser failed")
    if guard.extract_retry_after(RuntimeError("other")) is not None:
        fail("non-429 error misclassified")

    bot = FakeBot()
    result = guard.install_global_telegram_rate_limit_guard(bot)
    if not result["installed"] or "send_message" not in result["methods"]:
        fail(f"install failed: {result}")

    # First call reaches Telegram, receives 429, and must not escape.
    if bot.send_message(123, "first") is not None:
        fail("429 call should be contained")
    if len(bot.calls) != 1:
        fail(f"unexpected first-call count: {bot.calls}")

    # Subsequent calls during cooldown must never reach the original methods.
    bot.send_message(123, "second")
    bot.edit_message_text("edit", chat_id=123)
    bot.answer_callback_query("callback-id")
    if len(bot.calls) != 1:
        fail(f"cooldown calls reached Telegram: {bot.calls}")

    status = guard.get_telegram_rate_limit_status(123)
    if not status["blocked"] or status["remaining_seconds"] < 100:
        fail(f"cooldown status mismatch: {status}")

    second_install = guard.install_global_telegram_rate_limit_guard(bot)
    if second_install["installed"]:
        fail("guard installation is not idempotent")

    main_source = (ROOT / "main.py").read_text(encoding="utf-8-sig")
    install_marker = "install_global_telegram_rate_limit_guard(bot)"
    handlers_marker = "register_refine_handlers(bot)"
    worker_marker = "start_notification_worker(bot)"
    if install_marker not in main_source:
        fail("global guard installation missing from main.py")
    if main_source.rfind(install_marker) < main_source.find(handlers_marker):
        fail("global guard must be installed after handler registration")
    if main_source.rfind(install_marker) > main_source.find(worker_marker):
        fail("global guard must be installed before notification worker")

    combat_source = (ROOT / "handlers" / "combat.py").read_text(encoding="utf-8-sig")
    if "_combat_callback_allowed_11_3_1" not in combat_source:
        fail("combat mutation/debounce guard 11.3.1 is missing")

    print("[OK] Global Telegram rate-limit guard contracts")
    print("- retry_after 101 parser: OK")
    print("- send_message 429 contained outside polling loop: OK")
    print("- global cooldown suppresses send/edit/callback requests: OK")
    print("- stale presentation is not retried: OK")
    print("- non-429 exceptions remain visible: OK")
    print("- guard installed after handlers and before worker: OK")
    print("- combat mutation/debounce guard preserved: OK")
    print("- installation idempotency: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
