"""Presentation-only independent ROM V2 development shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

V2_MARKER: Final[str] = "ROM V2"


@dataclass(frozen=True, slots=True)
class ShellView:
    """Fully rendered shell response consumed by the Telegram boundary."""

    text: str
    reply_markup: dict[str, object]


def build_start_view() -> ShellView:
    """Render the visible V2 shell without reading or mutating game state."""
    return ShellView(
        text=(
            "🧪 ROM V2 — development shell\n\n"
            "Незалежне ядро V2 запущено. Ігрові функції підключатимуться "
            "поступово окремими наскрізними етапами."
        ),
        reply_markup={
            "inline_keyboard": [[{"text": "ℹ️ Стан V2", "callback_data": "v2:shell:status"}]]
        },
    )


def build_status_view() -> ShellView:
    """Render an honest readiness response without claiming gameplay wiring."""
    return ShellView(
        text=(
            "ℹ️ ROM V2 працює в ізольованому development-режимі.\n\n"
            "Telegram shell: CONNECTED\n"
            "Gameplay runtime: NOT_CONNECTED\n"
            "Production persistence: NOT_CONNECTED"
        ),
        reply_markup={
            "inline_keyboard": [[{"text": "🔙 Назад", "callback_data": "v2:shell:start"}]]
        },
    )


def route_shell_action(action: str) -> ShellView:
    """Route only the shell-owned stable actions and fail closed otherwise."""
    key = str(action or "").strip()
    if key in {"/start", "v2:shell:start"}:
        return build_start_view()
    if key == "v2:shell:status":
        return build_status_view()
    return ShellView(
        text="⚠️ Ця дія ще не підключена у ROM V2.",
        reply_markup={"inline_keyboard": [[{"text": "🔙 Назад", "callback_data": "v2:shell:start"}]]},
    )
