"""Tests for the framework-neutral ROM V2 Telegram adapter skeleton."""
from __future__ import annotations

import asyncio
import unittest

from rom_v2.infrastructure.telegram import (
    TelegramAdapterSkeleton,
    TelegramReply,
    TelegramUpdateEnvelope,
)


class TelegramAdapterSkeletonTest(unittest.TestCase):
    """Verify registration, dispatch, rejection, and isolation semantics."""

    def test_registered_command_dispatches_once(self) -> None:
        """Dispatch a production-shaped normalized update to its exact owner."""
        adapter = TelegramAdapterSkeleton()
        calls: list[int] = []

        async def handle_ping(update: TelegramUpdateEnvelope) -> TelegramReply:
            calls.append(update.update_id)
            return TelegramReply(chat_id=update.chat_id, text="pong")

        adapter.register_command("/ping", handle_ping)
        update = TelegramUpdateEnvelope(
            update_id=7,
            chat_id=11,
            user_id=13,
            text="/PING@development_bot argument",
        )
        reply = asyncio.run(adapter.dispatch_command(update))
        self.assertEqual(reply, TelegramReply(chat_id=11, text="pong"))
        self.assertEqual(calls, [7])

    def test_unknown_and_non_command_updates_are_ignored(self) -> None:
        """Return None without fallback routing or Telegram side effects."""
        adapter = TelegramAdapterSkeleton()
        unknown = TelegramUpdateEnvelope(1, 2, 3, "/unknown")
        text = TelegramUpdateEnvelope(4, 5, 6, "ordinary text")
        self.assertIsNone(asyncio.run(adapter.dispatch_command(unknown)))
        self.assertIsNone(asyncio.run(adapter.dispatch_command(text)))

    def test_duplicate_and_invalid_command_keys_are_rejected(self) -> None:
        """Keep one authoritative handler owner for each stable command key."""
        adapter = TelegramAdapterSkeleton()

        async def handler(update: TelegramUpdateEnvelope) -> None:
            return None

        adapter.register_command("/start", handler)
        with self.assertRaisesRegex(ValueError, "duplicate_telegram_command_key"):
            adapter.register_command("/START", handler)
        with self.assertRaisesRegex(ValueError, "invalid_telegram_command_key"):
            adapter.register_command("start", handler)
        with self.assertRaisesRegex(ValueError, "invalid_telegram_command_key"):
            adapter.register_command("/bad key", handler)

    def test_polling_is_explicitly_out_of_scope(self) -> None:
        """Prevent the skeleton stage from claiming an external runtime owner."""
        self.assertFalse(TelegramAdapterSkeleton().polling_supported())


if __name__ == "__main__":
    unittest.main()
