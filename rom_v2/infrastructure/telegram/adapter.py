"""Framework-neutral Telegram adapter skeleton for ROM V2."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Awaitable, Callable, Mapping, TypeAlias


@dataclass(frozen=True, slots=True)
class TelegramUpdateEnvelope:
    """Represent the minimal normalized input accepted at the Telegram boundary."""

    update_id: int
    chat_id: int
    user_id: int
    text: str

    def command_key(self) -> str | None:
        """Return a normalized command key without presentation arguments."""
        stripped = self.text.strip()
        if not stripped.startswith("/"):
            return None
        token = stripped.split(maxsplit=1)[0]
        command = token.split("@", maxsplit=1)[0].lower()
        return command if len(command) > 1 else None


@dataclass(frozen=True, slots=True)
class TelegramReply:
    """Describe an adapter response without calling the Telegram network."""

    chat_id: int
    text: str

    def __post_init__(self) -> None:
        """Reject empty presentation responses at the adapter boundary."""
        if not self.text.strip():
            raise ValueError("empty_telegram_reply")


TelegramCommandHandler: TypeAlias = Callable[
    [TelegramUpdateEnvelope], Awaitable[TelegramReply | None]
]


class TelegramAdapterSkeleton:
    """Register and dispatch command handlers without polling or network access."""

    def __init__(self) -> None:
        """Create an empty command registry owned by this adapter instance."""
        self._command_handlers: dict[str, TelegramCommandHandler] = {}

    @property
    def command_handlers(self) -> Mapping[str, TelegramCommandHandler]:
        """Expose a read-only view for composition and verification."""
        return MappingProxyType(self._command_handlers)

    def register_command(
        self,
        command_key: str,
        handler: TelegramCommandHandler,
    ) -> None:
        """Register exactly one handler for a stable slash-command key."""
        normalized = command_key.strip().lower()
        if not normalized.startswith("/") or len(normalized) < 2:
            raise ValueError("invalid_telegram_command_key")
        if any(character.isspace() for character in normalized):
            raise ValueError("invalid_telegram_command_key")
        if normalized in self._command_handlers:
            raise ValueError("duplicate_telegram_command_key")
        self._command_handlers[normalized] = handler

    async def dispatch_command(
        self,
        update: TelegramUpdateEnvelope,
    ) -> TelegramReply | None:
        """Dispatch one normalized command or return None when no route matches."""
        command_key = update.command_key()
        if command_key is None:
            return None
        handler = self._command_handlers.get(command_key)
        if handler is None:
            return None
        return await handler(update)

    def polling_supported(self) -> bool:
        """Declare that Stage 21.4.3 intentionally has no polling owner."""
        return False
