"""Telegram infrastructure boundary for ROM V2."""

from rom_v2.infrastructure.telegram.adapter import (
    TelegramAdapterSkeleton,
    TelegramCommandHandler,
    TelegramReply,
    TelegramUpdateEnvelope,
)
from rom_v2.infrastructure.telegram.callback_codec import (
    CallbackCodec,
    CallbackCodecError,
    CallbackRoute,
    DecodedCallback,
)
from rom_v2.infrastructure.telegram.callback_registry import (
    CallbackHandler,
    CallbackRegistry,
    CallbackRegistryError,
)

__all__ = [
    "CallbackCodec",
    "CallbackCodecError",
    "CallbackHandler",
    "CallbackRegistry",
    "CallbackRegistryError",
    "CallbackRoute",
    "DecodedCallback",
    "TelegramAdapterSkeleton",
    "TelegramCommandHandler",
    "TelegramReply",
    "TelegramUpdateEnvelope",
]
