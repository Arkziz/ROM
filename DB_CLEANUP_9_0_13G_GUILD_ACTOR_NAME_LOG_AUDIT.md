# ROM 9.0.13g — Guild Actor Name Log Audit

Generated: `2026-07-30T00:27:09`

## Safety

- Gameplay files changed: **0**
- Database rows changed: **0**
- Database SHA/size/mtime unchanged: **True**
- Database quick check: **ok**

## Event hooks

- Elite hook parameters: `['user_id', 'mob']`
- Contract hook parameters: `['user_id', 'contract']`
- Elite hook receives `user_id`: **True**
- Contract hook receives `user_id`: **True**
- Elite reason contains mob identity: **True**
- Contract reason contains target identity: **True**

## Character-name API

- `systems.character_system.get_character_name()` definitions: **1** at lines `[67]`
- `db.get_character_name()` definitions/facades: **1** at lines `[7429]`
- Guild System currently imports `get_character_name`: **False**
- Guild event hooks currently call `get_character_name()`: **False**
- Relevant `users` columns: `['character_name', 'user_id']`

## Isolated current output

- Elite reason: `Перемога над елітним мобом: ⭐️ Елітний 🔮 Audit cultist.`
- Contract reason: `Виконання контракту: 🔮 Audit cultist.`
- Actor name absent from both event formats: **True**

## Guild reward contracts

- Elite EXP reward constant: `25`
- Elite resource reward constant: `1`
- Contract EXP reward constant: `50`
- Contract resource reward constant: `3`
- Elite call increments: `kills=1`, `contracts=0`
- Contract call increments: `kills=0`, `contracts=1`

## Database context

- Guild log-like tables: `['guild_logs']`
- Historical event rows will not be rewritten because actor identity cannot be reconstructed reliably from existing reason text.

## Recommended format

- Contract: `Виконання контракту: <ціль>. (виконав: <ім’я персонажа>)`
- Elite kill: `Перемога над елітним мобом: <ціль>. (переміг: <ім’я персонажа>)`

## Recommended implementation

1. Add one central Guild helper that resolves a character display name by `user_id`.
2. Use the canonical Character API through a local/lazy import to avoid circular-import risk.
3. Normalize the returned value to a non-empty string.
4. Append `(виконав: <ім’я>)` to contract reasons.
5. Append `(переміг: <ім’я>)` to elite-kill reasons.
6. If no character name exists, preserve the current reason without a technical user ID or placeholder.
7. Preserve all Guild EXP, resource, kills, and contracts values exactly.
8. Add isolated tests for named and unnamed users without writing to the real database.

Suggested next patch: `patch_9_0_13h_guild_actor_name_log_hotfix.py`
