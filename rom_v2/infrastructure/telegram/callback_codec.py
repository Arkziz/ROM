"""Versioned and size-bounded callback-data codec for ROM V2."""
from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from urllib.parse import quote, unquote

MAX_CALLBACK_BYTES = 64
_COMPONENT_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,15}$")
_PARAMETER_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,11}$")


class CallbackCodecError(ValueError):
    """Expose a stable machine-readable callback codec failure code."""

    def __init__(self, code: str) -> None:
        """Store the stable failure code without presentation text."""
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True, order=True)
class CallbackRoute:
    """Identify one versioned callback namespace and action owner."""

    namespace: str
    action: str
    version: int = 1

    def __post_init__(self) -> None:
        """Reject unstable route identifiers before registry mutation."""
        if self.version < 1:
            raise CallbackCodecError("invalid_callback_version")
        if _COMPONENT_PATTERN.fullmatch(self.namespace) is None:
            raise CallbackCodecError("invalid_callback_namespace")
        if _COMPONENT_PATTERN.fullmatch(self.action) is None:
            raise CallbackCodecError("invalid_callback_action")


@dataclass(frozen=True, slots=True)
class DecodedCallback:
    """Represent one validated callback route and immutable parameter set."""

    route: CallbackRoute
    parameters: tuple[tuple[str, str], ...]

    def parameter_map(self) -> Mapping[str, str]:
        """Expose parameters through a read-only mapping."""
        return MappingProxyType(dict(self.parameters))


class CallbackCodec:
    """Encode and decode canonical callback data without Telegram dependencies."""

    def __init__(
        self,
        supported_versions: frozenset[int] = frozenset({1}),
        max_bytes: int = MAX_CALLBACK_BYTES,
    ) -> None:
        """Configure supported versions and the fail-closed byte limit."""
        if not supported_versions or any(version < 1 for version in supported_versions):
            raise CallbackCodecError("invalid_supported_versions")
        if max_bytes < 16 or max_bytes > MAX_CALLBACK_BYTES:
            raise CallbackCodecError("invalid_callback_byte_limit")
        self._supported_versions = supported_versions
        self._max_bytes = max_bytes

    def encode(
        self,
        route: CallbackRoute,
        parameters: Mapping[str, str] | None = None,
    ) -> str:
        """Encode one canonical route with deterministic sorted parameters."""
        self._require_supported(route.version)
        pairs = self._normalize_parameters(parameters or {})
        head = f"v{route.version}:{route.namespace}:{route.action}"
        if pairs:
            encoded_pairs = [
                f"{key}={quote(value, safe='-_~')}" for key, value in pairs
            ]
            encoded = f"{head}?{'&'.join(encoded_pairs)}"
        else:
            encoded = head
        if len(encoded.encode("utf-8")) > self._max_bytes:
            raise CallbackCodecError("callback_data_too_long")
        return encoded

    def decode(self, encoded: str) -> DecodedCallback:
        """Decode canonical callback data and reject ambiguous representations."""
        if not isinstance(encoded, str) or not encoded:
            raise CallbackCodecError("empty_callback_data")
        if len(encoded.encode("utf-8")) > self._max_bytes:
            raise CallbackCodecError("callback_data_too_long")
        head, separator, query = encoded.partition("?")
        parts = head.split(":")
        if len(parts) != 3 or not parts[0].startswith("v"):
            raise CallbackCodecError("malformed_callback_data")
        try:
            version = int(parts[0][1:])
        except ValueError as exc:
            raise CallbackCodecError("invalid_callback_version") from exc
        route = CallbackRoute(namespace=parts[1], action=parts[2], version=version)
        self._require_supported(route.version)
        parameters = self._decode_parameters(query if separator else "")
        decoded = DecodedCallback(route=route, parameters=parameters)
        # Canonical round-trip prevents alternate encodings from bypassing route checks.
        if self.encode(route, decoded.parameter_map()) != encoded:
            raise CallbackCodecError("non_canonical_callback_data")
        return decoded

    def _require_supported(self, version: int) -> None:
        """Reject versions that have no registered compatibility contract."""
        if version not in self._supported_versions:
            raise CallbackCodecError("unsupported_callback_version")

    def _normalize_parameters(
        self,
        parameters: Mapping[str, str],
    ) -> tuple[tuple[str, str], ...]:
        """Validate and sort parameters to guarantee deterministic output."""
        normalized: list[tuple[str, str]] = []
        for key, value in parameters.items():
            if _PARAMETER_KEY_PATTERN.fullmatch(key) is None:
                raise CallbackCodecError("invalid_callback_parameter_key")
            if not isinstance(value, str) or not value:
                raise CallbackCodecError("invalid_callback_parameter_value")
            normalized.append((key, value))
        return tuple(sorted(normalized))

    def _decode_parameters(self, query: str) -> tuple[tuple[str, str], ...]:
        """Decode parameters while rejecting duplicates and empty values."""
        if not query:
            return ()
        values: dict[str, str] = {}
        for component in query.split("&"):
            key, separator, encoded_value = component.partition("=")
            if not separator:
                raise CallbackCodecError("malformed_callback_parameter")
            if key in values:
                raise CallbackCodecError("duplicate_callback_parameter")
            if _PARAMETER_KEY_PATTERN.fullmatch(key) is None:
                raise CallbackCodecError("invalid_callback_parameter_key")
            value = unquote(encoded_value)
            if not value:
                raise CallbackCodecError("invalid_callback_parameter_value")
            values[key] = value
        return tuple(sorted(values.items()))
