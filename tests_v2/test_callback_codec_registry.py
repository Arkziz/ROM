"""Tests for the ROM V2 callback codec and single-owner registry."""
from __future__ import annotations

import asyncio
import unittest

from rom_v2.infrastructure.telegram import (
    CallbackCodec,
    CallbackCodecError,
    CallbackRegistry,
    CallbackRegistryError,
    CallbackRoute,
    TelegramReply,
)


class CallbackCodecRegistryTest(unittest.TestCase):
    """Verify deterministic encoding, strict decoding, and route ownership."""

    def test_codec_round_trip_is_deterministic(self) -> None:
        """Sort parameters and preserve Unicode through one canonical form."""
        codec = CallbackCodec()
        route = CallbackRoute(namespace="inventory", action="open")
        encoded = codec.encode(route, {"page": "2", "item": "меч"})
        self.assertEqual(encoded, "v1:inventory:open?item=%D0%BC%D0%B5%D1%87&page=2")
        decoded = codec.decode(encoded)
        self.assertEqual(decoded.route, route)
        self.assertEqual(dict(decoded.parameters), {"item": "меч", "page": "2"})

    def test_codec_rejects_ambiguous_or_oversized_data(self) -> None:
        """Fail closed on duplicate parameters, unsupported versions, and size."""
        codec = CallbackCodec()
        with self.assertRaisesRegex(CallbackCodecError, "duplicate_callback_parameter"):
            codec.decode("v1:inventory:open?page=1&page=2")
        with self.assertRaisesRegex(CallbackCodecError, "unsupported_callback_version"):
            codec.decode("v2:inventory:open")
        with self.assertRaisesRegex(CallbackCodecError, "callback_data_too_long"):
            codec.encode(
                CallbackRoute(namespace="inventory", action="open"),
                {"item": "x" * 60},
            )

    def test_registry_dispatches_exact_route_once(self) -> None:
        """Dispatch one decoded route to one authoritative handler."""
        codec = CallbackCodec()
        registry = CallbackRegistry(codec)
        route = CallbackRoute(namespace="profile", action="show")
        calls: list[tuple[tuple[str, str], ...]] = []

        async def handler(decoded: object) -> TelegramReply:
            parameters = getattr(decoded, "parameters")
            calls.append(parameters)
            return TelegramReply(chat_id=4, text="profile")

        registry.register(route, handler)
        encoded = codec.encode(route, {"page": "1"})
        reply = asyncio.run(registry.dispatch(encoded))
        self.assertEqual(reply, TelegramReply(chat_id=4, text="profile"))
        self.assertEqual(calls, [(('page', '1'),)])

    def test_registry_rejects_duplicate_and_unknown_routes(self) -> None:
        """Prevent overlapping owners and stale unknown callback dispatch."""
        codec = CallbackCodec()
        registry = CallbackRegistry(codec)
        route = CallbackRoute(namespace="map", action="open")

        async def handler(decoded: object) -> None:
            return None

        registry.register(route, handler)
        with self.assertRaisesRegex(CallbackRegistryError, "duplicate_callback_route"):
            registry.register(route, handler)
        unknown = codec.encode(CallbackRoute(namespace="map", action="travel"))
        with self.assertRaisesRegex(CallbackRegistryError, "unknown_callback_route"):
            asyncio.run(registry.dispatch(unknown))


if __name__ == "__main__":
    unittest.main()
