#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Global, process-local Telegram flood-control containment for ROM."""
from __future__ import annotations

# ROM 17.20.1.1 CRITICAL PRODUCTION LOGGING PRINT CONTRACT RECOVERY
from systems.production_logging import get_production_logger, production_log_print as PRODUCTION_LOG_PRINT
PRODUCTION_LOGGER=get_production_logger('systems.telegram_rate_limit')

import re
import threading
import time
from functools import wraps

_LOCK = threading.RLock()
_BLOCKED_UNTIL_BY_CHAT = {}
_GLOBAL_BLOCKED_UNTIL = 0.0
_INSTALLED_BOTS = set()
_SUPPRESSED_COUNTS = {}

# Methods that create or edit Telegram presentation. Game-state mutation must
# occur before these calls only once; failed presentation is never replayed.
_GUARDED_METHODS = (
    "send_message",
    "edit_message_text",
    "edit_message_reply_markup",
    "send_photo",
    "send_document",
    "send_animation",
    "send_video",
    "send_audio",
    "send_voice",
    "send_sticker",
    "answer_callback_query",
)


def extract_retry_after(error):
    """Return Telegram retry_after seconds for a 429 exception, else None."""
    text = str(error or "")
    if "too many requests" not in text.lower() and "error code: 429" not in text.lower():
        return None
    match = re.search(r"retry after\s+(\d+)", text, re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))
    try:
        result_json = getattr(error, "result_json", None) or {}
        parameters = result_json.get("parameters") or {}
        value = parameters.get("retry_after")
        if value is not None:
            return max(1, int(value))
    except Exception:
        pass
    return 1


def _extract_chat_id(method_name, args, kwargs):
    """Best-effort extraction for send/edit/callback API signatures."""
    if kwargs.get("chat_id") is not None:
        try:
            return int(kwargs["chat_id"])
        except Exception:
            return kwargs["chat_id"]
    if method_name == "answer_callback_query":
        return None
    if args:
        try:
            return int(args[0])
        except Exception:
            return args[0]
    return None


def _remaining_seconds(chat_id=None, now=None):
    now = time.monotonic() if now is None else float(now)
    with _LOCK:
        deadline = float(_GLOBAL_BLOCKED_UNTIL)
        if chat_id is not None:
            deadline = max(deadline, float(_BLOCKED_UNTIL_BY_CHAT.get(chat_id, 0.0)))
    if deadline <= now:
        return 0
    return max(1, int(deadline - now + 0.999))


def _register_flood_wait(chat_id, retry_after):
    global _GLOBAL_BLOCKED_UNTIL
    now = time.monotonic()
    # Telegram's retry_after is authoritative. The small safety margin avoids
    # firing on the exact boundary due to clock granularity.
    deadline = now + int(retry_after) + 1.0
    with _LOCK:
        _GLOBAL_BLOCKED_UNTIL = max(float(_GLOBAL_BLOCKED_UNTIL), deadline)
        if chat_id is not None:
            _BLOCKED_UNTIL_BY_CHAT[chat_id] = max(
                float(_BLOCKED_UNTIL_BY_CHAT.get(chat_id, 0.0)), deadline
            )
    return deadline


def _record_suppressed(method_name, chat_id, remaining):
    key = (method_name, chat_id)
    with _LOCK:
        count = int(_SUPPRESSED_COUNTS.get(key, 0)) + 1
        _SUPPRESSED_COUNTS[key] = count
    # Avoid console floods while still leaving periodic diagnostics.
    if count == 1 or count in (5, 10) or count % 25 == 0:
        PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram cooldown active: suppressed {method_name} "
            f"for chat {chat_id}; remaining about {remaining}s; count={count}")


def _guard_method(bot, method_name):
    original = getattr(bot, method_name, None)
    if not callable(original):
        return False
    if getattr(original, "_rom_global_429_guard_11_9_1", False):
        return False

    @wraps(original)
    def guarded(*args, **kwargs):
        chat_id = _extract_chat_id(method_name, args, kwargs)
        remaining = _remaining_seconds(chat_id)
        if remaining > 0:
            _record_suppressed(method_name, chat_id, remaining)
            return None
        try:
            return original(*args, **kwargs)
        except Exception as error:
            retry_after = extract_retry_after(error)
            if retry_after is None:
                raise
            _register_flood_wait(chat_id, retry_after)
            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram 429 contained globally: method={method_name}, "
                f"chat={chat_id}, retry_after={retry_after}s. "
                "Presentation was not retried; gameplay mutation will not be replayed.")
            return None

    guarded._rom_global_429_guard_11_9_1 = True
    guarded._rom_original_method_11_9_1 = original
    setattr(bot, method_name, guarded)
    return True


def install_global_telegram_rate_limit_guard(bot):
    """Install after all handler registration so this wrapper remains outermost."""
    marker = id(bot)
    with _LOCK:
        if marker in _INSTALLED_BOTS:
            return {"installed": False, "reason": "already_installed", "methods": ()}
    installed = []
    for method_name in _GUARDED_METHODS:
        if _guard_method(bot, method_name):
            installed.append(method_name)
    with _LOCK:
        _INSTALLED_BOTS.add(marker)
    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"✅ GLOBAL TELEGRAM 429 GUARD: {', '.join(installed)}")
    return {"installed": True, "methods": tuple(installed)}


def get_telegram_rate_limit_status(chat_id=None):
    """Read-only diagnostics for tests and future DEV tooling."""
    return {
        "blocked": _remaining_seconds(chat_id) > 0,
        "remaining_seconds": _remaining_seconds(chat_id),
        "chat_id": chat_id,
        "suppressed_total": sum(_SUPPRESSED_COUNTS.values()),
    }
