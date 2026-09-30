# Stage 19.25.14f: Hierarchy detail navigation cleanup

## Decision

`PASS_PENDING_MANUAL_GAME_CHECK`

Hierarchy quest details now remove the legacy `🔙 До журналу` descriptor before Telegram markup is built. The hierarchy-native `🔙 Квести розділу` button remains the only return route. Legacy journal builders and old Telegram callbacks remain registered for compatibility.
