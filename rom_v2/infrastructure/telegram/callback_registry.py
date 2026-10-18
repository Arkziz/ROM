"""Single-owner callback route registry for ROM V2 Telegram adapters."""
from __future__ import annotations

from types import MappingProxyType
from typing import Awaitable, Callable, Mapping, TypeAlias

from rom_v2.infrastructure.telegram.adapter import TelegramReply
from rom_v2.infrastructure.telegram.callback_codec import (
    CallbackCodec,
    CallbackRoute,
    DecodedCallback,
)

CallbackHandler: TypeAlias = Callable[
    [DecodedCallback], Awaitable[TelegramReply | None]
]


class CallbackRegistryError(ValueError):
    """Expose a stable machine-readable callback registry failure code."""

    def __init__(self, code: str) -> None:
        """Store the stable failure code without presentation text."""
        super().__init__(code)
        self.code = code


class CallbackRegistry:
    """Own callback routes and dispatch decoded callbacks exactly once."""

    def __init__(self, codec: CallbackCodec | None = None) -> None:
        """Create an empty registry with one canonical codec instance."""
        self._codec = codec or CallbackCodec()
        self._handlers: dict[CallbackRoute, CallbackHandler] = {}

    @property
    def handlers(self) -> Mapping[CallbackRoute, CallbackHandler]:
        """Expose a read-only registry view for composition and verification."""
        return MappingProxyType(self._handlers)

    def register(self, route: CallbackRoute, handler: CallbackHandler) -> None:
        """Register exactly one authoritative handler for a versioned route."""
        if route in self._handlers:
            raise CallbackRegistryError("duplicate_callback_route")
        self._handlers[route] = handler

    async def dispatch(self, encoded: str) -> TelegramReply | None:
        """Decode callback data and dispatch it to its exact route owner."""
        decoded = self._codec.decode(encoded)
        handler = self._handlers.get(decoded.route)
        if handler is None:
            raise CallbackRegistryError("unknown_callback_route")
        return await handler(decoded)
