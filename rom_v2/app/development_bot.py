"""Composition and polling loop for the independent V2 development bot."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Event
from typing import Iterable, Mapping

from rom_v2.infrastructure.telegram.bot_api import TelegramBotApi
from rom_v2.presentation.development_shell import ShellView, route_shell_action

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DevelopmentBotConfig:
    """Runtime-only configuration for the isolated Telegram shell."""

    token: str
    allowed_user_ids: frozenset[int]
    poll_timeout_seconds: int = 20

    def __post_init__(self) -> None:
        if not str(self.token or "").strip():
            raise ValueError("token must not be empty")
        if self.poll_timeout_seconds < 0:
            raise ValueError("poll_timeout_seconds must not be negative")


class IndependentDevelopmentBot:
    """Own the shell polling lifecycle without owning gameplay or durable state."""

    def __init__(self, config: DevelopmentBotConfig, api: TelegramBotApi | None = None) -> None:
        self._config = config
        self._api = api or TelegramBotApi(config.token)
        self._stop = Event()

    def stop(self) -> None:
        """Request graceful termination after the current Telegram request."""
        self._stop.set()

    def _authorized(self, user_id: int) -> bool:
        return not self._config.allowed_user_ids or int(user_id) in self._config.allowed_user_ids

    def _send_view(self, chat_id: int, view: ShellView) -> None:
        self._api.send_message(chat_id, view.text, reply_markup=view.reply_markup)

    def handle_update(self, update: Mapping[str, object]) -> None:
        """Parse one update, authorize first, and render only shell actions."""
        message = update.get("message")
        callback = update.get("callback_query")
        if isinstance(message, Mapping):
            sender = message.get("from")
            chat = message.get("chat")
            if not isinstance(sender, Mapping) or not isinstance(chat, Mapping):
                return
            user_id = int(sender.get("id", 0) or 0)
            chat_id = int(chat.get("id", 0) or 0)
            if not user_id or not chat_id or not self._authorized(user_id):
                return
            text = str(message.get("text", "") or "").strip()
            if text.startswith("/start"):
                self._send_view(chat_id, route_shell_action("/start"))
            return
        if isinstance(callback, Mapping):
            sender = callback.get("from")
            origin = callback.get("message")
            if not isinstance(sender, Mapping) or not isinstance(origin, Mapping):
                return
            chat = origin.get("chat")
            if not isinstance(chat, Mapping):
                return
            user_id = int(sender.get("id", 0) or 0)
            chat_id = int(chat.get("id", 0) or 0)
            if not user_id or not chat_id or not self._authorized(user_id):
                return
            self._send_view(chat_id, route_shell_action(str(callback.get("data", "") or "")))

    def run(self) -> None:
        """Run one stoppable long-polling loop owned only by the V2 process."""
        offset: int | None = None
        while not self._stop.is_set():
            response = self._api.get_updates(offset=offset, timeout=self._config.poll_timeout_seconds)
            updates = response.result if isinstance(response.result, list) else []
            for update in updates:
                if not isinstance(update, Mapping):
                    continue
                update_id = int(update.get("update_id", 0) or 0)
                if update_id:
                    offset = update_id + 1
                self.handle_update(update)


def build_development_bot(token: str, allowed_user_ids: Iterable[int] = ()) -> IndependentDevelopmentBot:
    """Compose the independent shell from transport and presentation owners."""
    config = DevelopmentBotConfig(
        token=str(token),
        allowed_user_ids=frozenset(int(value) for value in allowed_user_ids),
    )
    return IndependentDevelopmentBot(config)
