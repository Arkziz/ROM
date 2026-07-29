# ROM 9.0.13e — Combat Mana Potion Audit

Generated: `2026-07-29T23:49:07`

## Safety

- Gameplay files changed: **0**
- Database rows changed: **0**
- Database SHA/size/mtime unchanged: **True**
- Database quick check: **ok**

## Static potion definitions

- `201`: `{'name': '🔴 Мале зілля здоров’я', 'type': 'hp', 'restore': 50, 'buy_price': 5.0, 'sell_price': 1.0, 'max_stack': 10}`
- `203`: `{'name': '🔴 Середнє зілля здоров’я', 'type': 'hp', 'restore': 120, 'buy_price': 15.0, 'sell_price': 3.0, 'max_stack': 10}`
- `202`: `{'name': '🔵 Мале зілля мани', 'type': 'mp', 'restore': 40, 'buy_price': 6.0, 'sell_price': 1.2, 'max_stack': 10}`
- `204`: `{'name': '🔵 Середнє зілля мани', 'type': 'mp', 'restore': 100, 'buy_price': 18.0, 'sell_price': 3.6, 'max_stack': 10}`

## Current combat UI

- HP-only keyboard filter detected: **True**
- MP item types included in keyboard: **False**
- Empty-list message is HP-only: **True**

## Current potion backend

- MP potion definitions exist: **True**
- MP use explicitly rejected: **True**
- Current success result keys: `['heal', 'max_hp', 'message', 'new_hp', 'success']`
- Required MP result keys missing from current HP contract: `['max_mp', 'new_mp', 'restore_mp']`

## Combat callback and state

- Callback assumes HP result keys only: **True**
- Callback handles MP result keys: **False**
- Combat state already stores player MP/max MP: **True**
- Potion use currently spends no combat turn: **True**
- Shared potion cooldown state exists: **True**
- Cooldown helper handles HP potions: **True**
- Cooldown helper handles MP potions: **False**

## Character/MP infrastructure

- Mana resource is defined: **True**
- MP get/set/spend helpers are available: **True**
- `get_user_mp()` definitions in Character System: **2** at lines `[140, 232]`
- Runtime audit selected the last effective `get_user_mp()` definition, matching Python name binding.
- Relevant user columns: `['character_class', 'max_mp', 'mp']`

## Real database context

- Static potion rows: `[(201, '🔴 Мале зілля здоров’я', 'potion_hp', 'potion', 10), (202, '🔵 Мале зілля мани', 'potion_mp', 'potion', 10), (203, '🔴 Середнє зілля здоров’я', 'potion_hp_medium', 'potion', 10), (204, '🔵 Середнє зілля мани', 'potion_mp_medium', 'potion', 10)]`
- HP potion inventory context: `[{'item_id': 201, 'name': '🔴 Мале зілля здоров’я', 'type': 'potion_hp', 'stacks': 2, 'quantity': 6}]`
- MP potion inventory context: `[{'item_id': 202, 'name': '🔵 Мале зілля мани', 'type': 'potion_mp', 'stacks': 1, 'quantity': 10}]`

## Diagnosis

- Combat potion keyboard explicitly filters only HP potion item types.
- Potion backend explicitly rejects every MP potion as not implemented.
- Combat callback assumes every successful potion returns HP-only keys.
- Cooldown helper has no explicit MP potion mapping.
- Empty potion-list message mentions only health potions.

## Implementation scope for the next patch

1. Extend the combat potion keyboard with `potion_mp` and `potion_mp_medium` only for mana-resource classes.
2. Implement MP restoration in `systems.potion_system.use_potion_from_inventory()` using current/max MP helpers.
3. Return a typed result that lets the combat callback distinguish HP from MP restoration.
4. Synchronize successful MP restoration into `mob['player_mp']` and `mob['player_max_mp']`.
5. Keep potion use turn-free and use the existing shared stomach cooldown unless a separate balance rule is requested.
6. Map small MP potion to 3 turns and medium MP potion to 5 turns, matching HP size tiers.
7. Reject MP potion use at full mana without consuming the item or starting cooldown.
8. Hide MP potions from warrior, knight, scout, and rogue combat menus.
9. Preserve all current HP potion behavior and contracts.

## Conclusion

MP potions are fully defined as static items, and the Character/Combat systems already maintain MP state. However, combat support is incomplete in three separate layers: the potion-selection keyboard excludes MP types, the potion backend explicitly rejects MP restoration, and the combat callback assumes an HP-only success payload.

Suggested next patch: `patch_9_0_13f_combat_mana_potion_implementation.py`
