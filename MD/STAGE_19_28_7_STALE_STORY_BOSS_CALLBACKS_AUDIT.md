# Stage 19.28.7: аудит stale callback квесту 49

**Рішення:** `STALE_STORY_BOSS_CALLBACK_MUTATION_REQUIRED`

Read-only аудит `HELP`, `RETURN` та `INVOKE` для старих inline-кнопок у попередніх Telegram-повідомленнях.

## Підсумок

- Callback actions: HELP, RETURN, INVOKE.
- Lifecycle states: 6.
- Matrix cases: 18.
- Issues: 2.
- Stale exposure cases: 6.

## Виявлені проблеми

### `HELP_BYPASSES_LIFECYCLE_GATE`

- Severity: **HIGH**
- Actions: HELP
- States: AVAILABLE, COMPLETED, SKIPPED
- Причина: Old HELP buttons send invocation instructions before any active-quest eligibility check.

### `RETURN_BYPASSES_LIFECYCLE_GATE`

- Severity: **MEDIUM**
- Actions: RETURN
- States: AVAILABLE, COMPLETED, SKIPPED
- Причина: Old RETURN buttons send an obsolete route to the Mercenary Head before lifecycle validation.

## Lifecycle matrix

```text
AVAILABLE                HELP   expected=False current=True  stale=True
AVAILABLE                RETURN expected=False current=True  stale=True
AVAILABLE                INVOKE expected=False current=False stale=False
ACTIVE_CALLABLE          HELP   expected=True  current=True  stale=False
ACTIVE_CALLABLE          RETURN expected=True  current=True  stale=False
ACTIVE_CALLABLE          INVOKE expected=True  current=True  stale=False
ACTIVE_ENCOUNTER         HELP   expected=True  current=True  stale=False
ACTIVE_ENCOUNTER         RETURN expected=True  current=True  stale=False
ACTIVE_ENCOUNTER         INVOKE expected=False current=False stale=False
ACTIVE_DEFEATED_1_OF_1   HELP   expected=True  current=True  stale=False
ACTIVE_DEFEATED_1_OF_1   RETURN expected=True  current=True  stale=False
ACTIVE_DEFEATED_1_OF_1   INVOKE expected=False current=False stale=False
COMPLETED                HELP   expected=False current=True  stale=True
COMPLETED                RETURN expected=False current=True  stale=True
COMPLETED                INVOKE expected=False current=False stale=False
SKIPPED                  HELP   expected=False current=True  stale=True
SKIPPED                  RETURN expected=False current=True  stale=True
SKIPPED                  INVOKE expected=False current=False stale=False
```

## Контракт наступного patch

1. Один lifecycle gate має виконуватися до branching за action.
2. `HELP` і `RETURN` дозволені лише для активного квесту 49.
3. `INVOKE` додатково вимагає explicit `allowed=True` та відсутність active encounter.
4. `ACTIVE 1/1` дозволяє лише допомогу/повернення до доповіді, але не повторний виклик.
5. `COMPLETED`, `SKIPPED` і `AVAILABLE` відхиляють старі callback-кнопки нейтральним alert без надсилання нового повідомлення.
6. Не видаляти старі Telegram-повідомлення й не змінювати boss/combat lifecycle.
