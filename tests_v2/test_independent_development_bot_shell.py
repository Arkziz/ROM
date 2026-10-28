from __future__ import annotations

import unittest

from rom_v2.app.development_bot import DevelopmentBotConfig, IndependentDevelopmentBot
from rom_v2.infrastructure.telegram.bot_api import TelegramApiResponse
from rom_v2.presentation.development_shell import build_start_view, route_shell_action


class FakeApi:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str, object]] = []

    def send_message(self, chat_id: int, text: str, *, reply_markup=None):
        self.sent.append((chat_id, text, reply_markup))
        return TelegramApiResponse(ok=True, result={})

    def get_updates(self, *, offset=None, timeout=20):
        return TelegramApiResponse(ok=True, result=[])


class IndependentDevelopmentBotShellTests(unittest.TestCase):
    def test_start_view_is_honest_and_versioned(self) -> None:
        view = build_start_view()
        self.assertIn("ROM V2", view.text)
        self.assertIn("development shell", view.text)
        self.assertNotIn("RUNTIME_READY", view.text)

    def test_unknown_action_fails_closed(self) -> None:
        self.assertIn("ще не підключена", route_shell_action("v2:unknown").text)

    def test_allowlist_is_checked_before_response(self) -> None:
        api = FakeApi()
        bot = IndependentDevelopmentBot(DevelopmentBotConfig("token", frozenset({10})), api=api)
        bot.handle_update({"message": {"from": {"id": 11}, "chat": {"id": 11}, "text": "/start"}})
        self.assertEqual(api.sent, [])
        bot.handle_update({"message": {"from": {"id": 10}, "chat": {"id": 10}, "text": "/start"}})
        self.assertEqual(len(api.sent), 1)


if __name__ == "__main__":
    unittest.main()
