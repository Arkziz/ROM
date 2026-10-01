"""Pure policy adapter for temporary story-boss inline invocation.

The adapter owns no Telegram bot and creates no encounter itself. Delivery handlers pass
canonical quest/encounter state into these pure functions, then delegate an approved invoke
to the existing combat owner. This keeps stale callbacks and anti-farm checks centralized.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

CALLBACK_PREFIX = "sqboss:v1"
INVOKE_CALLBACK = "sqboss:v1:invoke:49"
HELP_CALLBACK = "sqboss:v1:help:49"
RETURN_CALLBACK = "sqboss:v1:return:49"

class StoryBossAction(str, Enum):
    INVOKE = "invoke"
    HELP = "help"
    RETURN = "return"

@dataclass(frozen=True)
class StoryBossInvocationState:
    quest_number: int
    quest_status: str
    progress_current: int
    progress_target: int
    expected_location_id: str
    current_location_id: str
    has_active_encounter: bool
    has_active_travel: bool
    is_busy: bool

@dataclass(frozen=True)
class StoryBossInlinePresentation:
    text_suffix: str
    rows: tuple[tuple[tuple[str, str], ...], ...]

class StoryBossInvocationDecision(str, Enum):
    ALLOW = "allow"
    WRONG_QUEST = "wrong_quest"
    QUEST_NOT_ACTIVE = "quest_not_active"
    ALREADY_DEFEATED = "already_defeated"
    WRONG_LOCATION = "wrong_location"
    ACTIVE_ENCOUNTER = "active_encounter"
    ACTIVE_TRAVEL = "active_travel"
    BUSY = "busy"


def parse_story_boss_callback(data: str) -> tuple[StoryBossAction, int] | None:
    parts = str(data or "").split(":")
    if len(parts) != 4 or parts[:2] != ["sqboss", "v1"]:
        return None
    try:
        action = StoryBossAction(parts[2])
        quest_number = int(parts[3])
    except (ValueError, TypeError):
        return None
    return action, quest_number


def evaluate_story_boss_invocation(state: StoryBossInvocationState) -> StoryBossInvocationDecision:
    if state.quest_number != 49:
        return StoryBossInvocationDecision.WRONG_QUEST
    if str(state.quest_status).upper() != "ACTIVE":
        return StoryBossInvocationDecision.QUEST_NOT_ACTIVE
    if state.progress_current >= state.progress_target:
        return StoryBossInvocationDecision.ALREADY_DEFEATED
    if state.current_location_id != state.expected_location_id:
        return StoryBossInvocationDecision.WRONG_LOCATION
    if state.has_active_encounter:
        return StoryBossInvocationDecision.ACTIVE_ENCOUNTER
    if state.has_active_travel:
        return StoryBossInvocationDecision.ACTIVE_TRAVEL
    if state.is_busy:
        return StoryBossInvocationDecision.BUSY
    return StoryBossInvocationDecision.ALLOW


def build_story_boss_look_around_presentation(state: StoryBossInvocationState) -> StoryBossInlinePresentation | None:
    if state.quest_number != 49 or str(state.quest_status).upper() != "ACTIVE":
        return None
    if state.current_location_id != state.expected_location_id:
        return None
    if state.progress_current >= state.progress_target:
        return StoryBossInlinePresentation(
            text_suffix="✅ Ватажка переможено. Повернися до Голови Найманців і доповідь про перемогу.",
            rows=((('🧭 Куди повернутися', RETURN_CALLBACK),),),
        )
    return StoryBossInlinePresentation(
        text_suffix=("🐺 Сліди Ватажка\n\nПоблизу помітні свіжі сліди Ватажка зграї. "
                     "Ти можеш викликати його на бій або продовжити звичайне полювання."),
        rows=(
            (("🐺 Викликати Ватажка", INVOKE_CALLBACK),),
            (("🧭 Як знайти Ватажка", HELP_CALLBACK),),
        ),
    )


def story_boss_help_text() -> str:
    return ("🐺 Як знайти Ватажка\n\nВирушай у локацію «Початок Шляху» та натисни "
            "«👀 Роззирнутися». Там Ватажка можна викликати на бій. "
            "Також Ватажок може зустрітися випадково під час звичайного полювання. "
            "Якщо ще не готовий, продовжуй полювання та повернися пізніше.")


def decision_message(decision: StoryBossInvocationDecision) -> str:
    return {
        StoryBossInvocationDecision.ALLOW: "",
        StoryBossInvocationDecision.WRONG_QUEST: "Ця дія більше недоступна.",
        StoryBossInvocationDecision.QUEST_NOT_ACTIVE: "Квест на Ватажка зараз не активний.",
        StoryBossInvocationDecision.ALREADY_DEFEATED: "✅ Ватажка вже переможено. Повернися до Голови Найманців.",
        StoryBossInvocationDecision.WRONG_LOCATION: "Ватажка можна викликати лише у локації «Початок Шляху».",
        StoryBossInvocationDecision.ACTIVE_ENCOUNTER: "⚔️ Поточний бій або encounter потрібно завершити.",
        StoryBossInvocationDecision.ACTIVE_TRAVEL: "🧭 Спочатку заверши подорож.",
        StoryBossInvocationDecision.BUSY: "Зараз персонаж зайнятий іншою дією.",
    }[decision]
