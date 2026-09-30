# Stage 19.25.12: Story quest hierarchy UI audit

## Decision

`READY_FOR_STAGE_19_25_13_HIERARCHY_METADATA`

## Approved Ukrainian hierarchy

`📜 Сюжетні історії → історія локації → розділи → квести → деталі квесту`

The canonical Ukrainian term is **розділ**. The term **глава** is forbidden in new user-facing quest navigation.

## Current production boundary

- Location: `Початок Шляху` (`start_path` only as internal metadata).
- Active production quests: `1-30`.
- Visible production sections: `1-10`, `11-20`, `21-30`.
- Quests `31+` must not appear until production activation.

## Production sections

- Розділ 1: quests 1-10, required level 1.
- Розділ 2: quests 11-20, required level 2.
- Розділ 3: quests 21-30, required level 3.

## Approved UX rules

- First screen: `📜 Сюжетні історії`.
- First story button: `🌄 Початок Шляху`.
- Show production sections only.
- One quest button per row with status, number, and short title.
- Completed quests remain readable and have no repeatable action.
- Hierarchical back navigation: quest details → section quests → sections → stories → character.
- Existing Telegram messages with legacy page callbacks must remain safe.
- No database migration is required.

## Static owner candidates

- `handlers/city.py`: 46 quest-related function records.
- `handlers/combat.py`: 21 quest-related function records.
- `handlers/runes.py`: 22 quest-related function records.
- `handlers/story_quest_npc_runtime.py`: 21 quest-related function records.
- `handlers/story_quests.py`: 15 quest-related function records.
- `systems/story_quest_boss_call_system.py`: 1 quest-related function records.
- `systems/story_quest_boss_completion_system.py`: 2 quest-related function records.
- `systems/story_quest_combat_progress_system.py`: 1 quest-related function records.
- `systems/story_quest_completion_system.py`: 4 quest-related function records.
- `systems/story_quest_item_drop_system.py`: 1 quest-related function records.
- `systems/story_quest_location_presentation.py`: 1 quest-related function records.
- `systems/story_quest_npc_acceptance_system.py`: 4 quest-related function records.
- `systems/story_quest_overlevel_system.py`: 2 quest-related function records.
- `systems/story_quest_player_level.py`: 1 quest-related function records.
- `systems/story_quest_reward_system.py`: 2 quest-related function records.
- `systems/story_quest_system.py`: 10 quest-related function records.
- `data/story_quest_content.py`: 1 quest-related function records.
- `data/story_quest_definitions.py`: 5 quest-related function records.
- `data/story_quest_npcs.py`: 6 quest-related function records.
- `data/story_quests/__init__.py`: 0 quest-related function records.
- `data/story_quests/start_path_01_10.py`: 0 quest-related function records.
- `data/story_quests/start_path_11_20.py`: 0 quest-related function records.

## Callback evidence

- `handlers/admin_crystal_credit.py:25` → `requested_amount` (16 bytes).
- `handlers/admin_crystal_credit.py:78` → `ac:history_close` (16 bytes).
- `handlers/admin_crystal_credit.py:79` → `ac:history_detail:` (18 bytes).
- `handlers/admin_crystal_credit.py:83` → `ac:history:` (11 bytes).
- `handlers/admin_crystal_credit.py:43` → `requested_amount` (16 bytes).
- `handlers/admin_crystal_credit.py:46` → `ac:history_close` (16 bytes).
- `handlers/admin_crystal_credit.py:55` → `ac:history_close` (16 bytes).
- `handlers/admin_crystal_credit.py:42` → `requested_amount` (16 bytes).
- `handlers/admin_crystal_credit.py:46` → `ac:history:` (11 bytes).
- `handlers/admin_crystal_credit.py:51` → `ac:history_detail:` (18 bytes).
- `handlers/admin_crystal_credit.py:52` → `ac:history:` (11 bytes).
- `handlers/admin_crystal_credit.py:54` → `ac:history:` (11 bytes).
- `handlers/admin_crystal_credit.py:110` → `requested_amount` (16 bytes).
- `handlers/admin_crystal_credit.py:92` → `requested_amount` (16 bytes).
- `handlers/auction_house.py:3097` → `AUCTION_HISTORY_STATE` (21 bytes).
- `handlers/auction_house.py:3200` → `AUCTION_HISTORY_STATE` (21 bytes).
- `handlers/auction_house.py:4552` → `history_date` (12 bytes).
- `handlers/combat.py:2079` → `story_boss_call` (15 bytes).
- `handlers/player_interaction.py:527` → `request_expired` (15 bytes).
- `handlers/player_interaction.py:530` → `request_not_pending` (19 bytes).
- `handlers/player_interaction.py:314` → `request_id` (10 bytes).
- `handlers/player_interaction.py:315` → `request_id` (10 bytes).
- `handlers/profile.py:803` → `profile_history_trade_detail` (28 bytes).
- `handlers/profile.py:803` → `profile_history_pvp_detail` (26 bytes).
- `handlers/profile.py:1103` → `profile_history` (15 bytes).
- `handlers/profile.py:1109` → `profile_history_trade_detail:` (29 bytes).
- `handlers/profile.py:1117` → `profile_history_pvp_detail:` (27 bytes).
- `handlers/profile.py:789` → `profile_history_trade:0` (23 bytes).
- `handlers/profile.py:791` → `profile_history_pvp:0` (21 bytes).
- `handlers/profile.py:819` → `profile_history` (15 bytes).

## Risks

- Existing page-based callbacks/messages require compatibility routing after the hierarchy UI is introduced.
- Technical location identifiers exist in source strings; implementation must distinguish internal metadata from user-facing text.

## Next stage

Stage 19.25.13 should add canonical hierarchy metadata only. The live UI must remain unchanged until the metadata passes regression checks.
