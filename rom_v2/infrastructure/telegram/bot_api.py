"""Pure Telegram Bot API HTTP transport for the independent V2 shell.

This adapter owns only request serialization, HTTP delivery, and response
validation. Gameplay state and durable state are deliberately outside this
boundary and must be supplied by the V2 composition root/application layer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class TelegramTransportError(RuntimeError):
    """Raised when Telegram cannot accept or return a valid API response."""


class HttpOpener(Protocol):
    """Minimal injectable HTTP opener used by deterministic tests."""

    def __call__(self, request: Request, *, timeout: float) -> Any: ...


@dataclass(frozen=True, slots=True)
class TelegramApiResponse:
    """Validated machine-readable response from one Telegram API method."""

    ok: bool
    result: object | None
    description: str | None = None


class TelegramBotApi:
    """Small synchronous Telegram HTTP client with no gameplay dependencies."""

    def __init__(self, token: str, *, timeout_seconds: float = 20.0, opener: HttpOpener | None = None) -> None:
        normalized = str(token or "").strip()
        if not normalized:
            raise ValueError("Telegram bot token must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._base_url = f"https://api.telegram.org/bot{normalized}"
        self._timeout_seconds = float(timeout_seconds)
        self._opener = opener or urlopen

    def call(self, method: str, payload: Mapping[str, object] | None = None) -> TelegramApiResponse:
        """Call one Telegram method and fail closed on transport/API errors."""
        method_name = str(method or "").strip()
        if not method_name or not method_name.replace("_", "").isalnum():
            raise ValueError("Invalid Telegram API method")
        body = json.dumps(dict(payload or {}), ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self._base_url}/{method_name}",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                raw = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise TelegramTransportError(f"Telegram request failed: {type(error).__name__}") from error
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TelegramTransportError("Telegram returned invalid JSON") from error
        if not isinstance(decoded, dict):
            raise TelegramTransportError("Telegram returned a non-object response")
        result = TelegramApiResponse(
            ok=bool(decoded.get("ok")),
            result=decoded.get("result"),
            description=str(decoded.get("description")) if decoded.get("description") is not None else None,
        )
        if not result.ok:
            raise TelegramTransportError(result.description or "Telegram API rejected the request")
        return result

    def send_message(self, chat_id: int, text: str, *, reply_markup: Mapping[str, object] | None = None) -> TelegramApiResponse:
        """Send one already-presented message; no business decisions occur here."""
        payload: dict[str, object] = {"chat_id": int(chat_id), "text": str(text)}
        if reply_markup is not None:
            payload["reply_markup"] = dict(reply_markup)
        return self.call("sendMessage", payload)

    def get_updates(self, *, offset: int | None = None, timeout: int = 20) -> TelegramApiResponse:
        """Read updates for the development long-polling loop."""
        payload: dict[str, object] = {"timeout": max(0, int(timeout)), "allowed_updates": ["message", "callback_query"]}
        if offset is not None:
            payload["offset"] = int(offset)
        return self.call("getUpdates", payload)
