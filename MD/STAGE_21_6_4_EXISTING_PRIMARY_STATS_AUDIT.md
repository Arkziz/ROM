# Stage 21.6.4 — Existing V1 primary-stats audit

## Scope

Read-only audit of STR/DEX/INT/WIS/STA storage, initial values, allocation, floors, validation, reset behavior, and production ownership in V1. No V1 module was imported or executed and no database was opened.

## Primary keys

`str`, `dex`, `int`, `wis`, `sta`

## Evidence summary

- tracked V1 Python files scanned: `1010`
- candidate files: `194`
- blockers: `[]`
- review topics: `['INITIAL_VALUES', 'ALLOCATION', 'RESET', 'FLOORS_AND_BOUNDS', 'READ_OWNERS', 'WRITE_OWNERS']`

## Discovery categories

### PRIMARY_KEY_DECLARATIONS

Evidence count: `171`

- `data/bosses.py:9` — `BOSS_PRIMARY_STAT_MULTIPLIER = 2.2`
- `data/defense_policy.py:8` — `def calculate_stat_defense(primary_stat):`
- `data/defense_policy.py:10` — `return max(0.0, float(primary_stat or 0)) * DEFENSE_STAT_COEFFICIENT`
- `data/defense_policy.py:13` — `def calculate_total_defense(item_defense, primary_stat):`
- `data/defense_policy.py:15` — `return max(0.0, float(item_defense or 0)) + calculate_stat_defense(primary_stat)`
- `data/equipment_identity_stat_policy.py:12` — `PRIMARY_STATS=("str","dex","int","wis","sta")`
- `data/equipment_identity_stat_policy.py:13` — `BONUS_KEYS={stat:"bonus_"+stat for stat in PRIMARY_STATS}`
- `data/equipment_identity_stat_policy.py:36` — `JEWELRY_STAT_WEIGHTS=tuple((stat,20) for stat in PRIMARY_STATS)`
- `data/equipment_identity_stat_policy.py:49` — `def redistribute_identity_primary_stats(stats,slot_key,*,item_subtype="",armor_type="",chooser):`
- `data/equipment_identity_stat_policy.py:54` — `for stat in PRIMARY_STATS:`
- `data/equipment_identity_stat_policy.py:73` — `if any(stat not in PRIMARY_STATS or weight<=0 for stat,weight in profile):errors.append(f"{label}.{key}: invalid profile")`
- `data/equipment_identity_stat_policy.py:74` — `if set(stat for stat,_weight in JEWELRY_STAT_WEIGHTS)!=set(PRIMARY_STATS) or len({weight for _stat,weight in JEWELRY_STAT_WEIGHTS})!=1:errors.append("jewelry must be universal equal-weight")`
- `data/equipment_stat_policy.py:15` — `PRIMARY_STATS = ("str", "dex", "int", "wis", "sta")`
- `data/equipment_stat_policy.py:110` — `if stat_key not in PRIMARY_STATS or stat_key in seen:`
- `data/equipment_stat_policy.py:183` — `def redistribute_primary_stat_budget(stats, class_key, equipment_kind, *, item_subtype="", chooser):`
- `data/equipment_stat_policy.py:195` — `for stat_key in PRIMARY_STATS:`
- `data/equipment_stat_policy.py:209` — `if sum(int(result.get("bonus_" + stat, 0) or 0) for stat in PRIMARY_STATS) != sum(chunks):`
- `data/equipment_stat_policy.py:220` — `"PRIMARY_STATS", "PHYSICAL_CLASSES", "MAGICAL_CLASSES",`
- `data/equipment_stat_policy.py:225` — `"get_allowed_equipment_stats", "redistribute_primary_stat_budget",`
- `data/stat_system_config.py:5` — `PRIMARY_STAT_KEYS = ("str", "dex", "int", "wis", "sta")`
- `data/stat_system_config.py:38` — `expected_stats = set(PRIMARY_STAT_KEYS)`
- `db_modules/dev_compat.py:872` — `ARMOR_PRIMARY_STAT_PROFILES = {`
- `db_modules/dev_compat.py:975` — `def add_primary_stat_to_stats(stats, stat_key, value):`
- `db_modules/dev_compat.py:1000` — `def get_existing_primary_stat_budget(stats):`
- `db_modules/dev_compat.py:1014` — `def clear_primary_stat_bonuses(stats):`
- `db_modules/dev_compat.py:1025` — `def apply_armor_type_primary_stat_profile_to_stats(stats, armor_type):`
- `db_modules/dev_compat.py:1040` — `profile = ARMOR_PRIMARY_STAT_PROFILES.get(armor_type)`
- `db_modules/dev_compat.py:1045` — `existing_budget = get_existing_primary_stat_budget(stats)`
- `db_modules/dev_compat.py:1050` — `clear_primary_stat_bonuses(stats)`
- `db_modules/dev_compat.py:1065` — `primary_stat = pick_weighted_stat(`

### CHARACTER_STORAGE

Evidence count: `240`

- `config.py:9` — `raw = str(os.getenv(name, default)).strip()`
- `config.py:10` — `value = int(raw)`
- `config.py:16` — `raw = str(os.getenv("ROM_ADMIN_USER_IDS", "")).strip()`
- `config.py:17` — `return frozenset(int(part.strip()) for part in raw.split(",") if part.strip())`
- `config.py:29` — `_GAME_CHAT_URL_RAW = str(os.getenv("GAME_CHAT_URL", "") or "").strip()`
- `config.py:30` — `_NEWS_CHANNEL_URL_RAW = str(os.getenv("NEWS_CHANNEL_URL", "") or "").strip()`
- `config.py:31` — `_SUPPORT_URL_RAW = str(os.getenv("SUPPORT_URL", "") or "").strip()`
- `config.py:35` — `value = str(value or "").strip()`
- `config.py:42` — `host = str(parsed.hostname or "").casefold()`
- `config.py:43` — `allowed = {str(item).casefold() for item in allowed_hosts}`
- `data/about_game.py:98` — `def get_about_game_section(key): return ABOUT_GAME_SECTIONS.get(str(key or ""))`
- `data/bosses.py:126` — `return BOSS_DEFINITIONS.get(str(boss_key or ""))`
- `data/bosses.py:130` — `boss_key = BOSS_KEY_BY_LOCATION.get(str(location_id or ""))`
- `data/defense_policy.py:9` — `"""Return the raw defense layer produced by STA or WIS."""`
- `data/drop_tables.py:243` — `("STR", 0.20), ("STA", 0.20), ("DEX", 0.20),`
- `data/drop_tables.py:245` — `("INT", 0.20), ("WIS", 0.20),`
- `data/equipment_identity_stat_policy.py:12` — `PRIMARY_STATS=("str","dex","int","wis","sta")`
- `data/equipment_identity_stat_policy.py:16` — `"sword_1h":(("str",50),("sta",35),("dex",15)),`
- `data/equipment_identity_stat_policy.py:17` — `"sword_2h":(("str",60),("sta",30),("dex",10)),`
- `data/equipment_identity_stat_policy.py:18` — `"dagger_1h":(("dex",60),("str",30),("sta",10)),`
- `data/equipment_identity_stat_policy.py:19` — `"wand_1h":(("int",55),("wis",35),("sta",10)),`
- `data/equipment_identity_stat_policy.py:20` — `"staff_2h":(("int",55),("wis",35),("sta",10)),`
- `data/equipment_identity_stat_policy.py:21` — `"bow_2h":(("str",45),("dex",45),("sta",10)),`
- `data/equipment_identity_stat_policy.py:22` — `"crossbow_2h":(("str",45),("dex",45),("sta",10)),`
- `data/equipment_identity_stat_policy.py:25` — `"warrior_shield":(("str",65),("sta",35)),`
- `data/equipment_identity_stat_policy.py:26` — `"shield":(("sta",65),("str",35)),`
- `data/equipment_identity_stat_policy.py:27` — `"dagger":(("dex",65),("str",35)),`
- `data/equipment_identity_stat_policy.py:28` — `"talisman":(("int",55),("wis",45)),`
- `data/equipment_identity_stat_policy.py:31` — `"cloth":(("int",40),("wis",40),("sta",20)),`
- `data/equipment_identity_stat_policy.py:32` — `"leather":(("dex",50),("str",30),("sta",20)),`

### INITIAL_VALUES

Evidence count: `126`

- `data/player_combat_chances.py:34` — `return CRIT_BASE_CHANCE + max(0.0, stat - CRIT_STAT_BASELINE) * CRIT_PER_STAT`
- `data/runes.py:42` — `item_id = RUNE_ITEM_ID_START + stat_index * len(RUNE_LEVELS) + level - 1`
- `data/stat_scaling.py:137` — `base_hp = calculate_base_max_hp(round_stat(level), round_stat(total_sta))`
- `db_modules/dev_compat.py:149` — `base_stat = 10 + (target_level - 1)`
- `db_modules/dev_compat.py:164` — `base_stat,`
- `db_modules/dev_compat.py:165` — `base_stat,`
- `db_modules/dev_compat.py:166` — `base_stat,`
- `db_modules/dev_compat.py:167` — `base_stat,`
- `db_modules/dev_compat.py:168` — `base_stat,`
- `db_modules/dev_compat.py:193` — `"base_stat": base_stat,`
- `db_modules/dev_compat.py:199` — `f"💪 Базові характеристики: {base_stat}\n"`
- `db_modules/dev_compat.py:1114` — `base_pdef = int(stats.get("pdef", 0) or 0)`
- `db_modules/dev_compat.py:1115` — `base_mdef = int(stats.get("mdef", 0) or 0)`
- `db_modules/generated_equipment.py:865` — `base_pdef = int(stats.get("pdef", 0) or 0)`
- `db_modules/generated_equipment.py:866` — `base_mdef = int(stats.get("mdef", 0) or 0)`
- `events/item_namespace.py:26` — `start=EVENT_STATIC_ITEM_MIN + index * EVENT_ITEM_BLOCK_SIZE`
- `events/item_namespace.py:42` — `if start < EVENT_STATIC_ITEM_MIN or end > EVENT_STATIC_ITEM_MAX:`
- `events/item_namespace.py:46` — `if (start - EVENT_STATIC_ITEM_MIN) % EVENT_ITEM_BLOCK_SIZE != 0:`
- `handlers/event_ui.py:25` — `if start is None or end is None:status="upcoming"`
- `handlers/event_ui.py:29` — `rows.append({"event_key":cfg.EVENT_KEY,"title":getattr(cfg,"TITLE",cfg.EVENT_KEY),"status":status,"start":start,"end":end,"completed_read_only":status=="completed"})`
- `handlers/guild.py:184` — `def start_guild_create_state(user_id):`
- `handlers/guild.py:575` — `start_guild_create_state(user_id)`
- `handlers/guild.py:596` — `start_guild_create_state(user_id)`
- `main.py:146` — `# ROM 12.6.5: process restarts invalidate all unfinished trade UI/input state.`
- `systems/boss_system.py:322` — `defaults = create_boss_state()`
- `systems/combat_system.py:281` — `base_damage = weapon_damage + player_stat_attack - (mob_def * 0.5)`
- `systems/inactivity_reminder_system.py:21` — `c.executescript("""CREATE TABLE IF NOT EXISTS inactivity_reminders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,inactivity_started_at TEXT NOT NULL,eligible_at TEXT NOT NULL,attempted_at TEXT NOT NULL,delivery_status TEXT NOT NULL CHECK(delivery_status IN ('pending','sent','blocked','failed')),error_type TEXT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(user_id,inactivity_started_at),FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);CREATE INDEX IF NOT EXISTS idx_inactivity_reminders_user ON inactivity_reminders(user_id,id DESC);CREATE INDEX IF`
- `systems/inactivity_reminder_system.py:38` — `stamp=_stamp(current);cur=c.execute("INSERT OR IGNORE INTO inactivity_reminders(user_id,inactivity_started_at,eligible_at,attempted_at,delivery_status,error_type,created_at,updated_at) VALUES(?,?,?,?, 'pending',NULL,?,?)",(int(user_id),started,eligible,stamp,stamp,stamp));claimed=cur.rowcount==1;c.commit();return {'success':True,'claimed':claimed,'reason':'claimed' if claimed else 'already_attempted'}`
- `systems/inactivity_reminder_system.py:41` — `def finalize_inactivity_reminder(user_id,inactivity_started_at,status,error_type=None,now=None,db_path=None):`
- `systems/inactivity_reminder_system.py:45` — `cur=c.execute("UPDATE inactivity_reminders SET delivery_status=?,error_type=?,updated_at=? WHERE user_id=? AND inactivity_started_at=? AND delivery_status='pending'",(status,str(error_type or '')[:120] or None,_stamp(now),int(user_id),str(inactivity_started_at)));c.commit();return {'success':cur.rowcount==1,'updated':cur.rowcount}`

### ALLOCATION

Evidence count: `86`

- `data/equipment_stat_policy.py:21` — `# PATK/MATK coefficients and not additive stat budgets.`
- `data/equipment_stat_policy.py:114` — `seen.add(stat_key)`
- `db_modules/dev_compat.py:535` — `def add_stat_value(stats, stat_key, value):`
- `db_modules/dev_compat.py:609` — `add_stat_value(stats, main_stat, value)`
- `db_modules/dev_compat.py:651` — `add_stat_value(stats, bonus, value)`
- `db_modules/dev_compat.py:702` — `add_stat_value(stats, stat_choice, value)`
- `db_modules/dev_compat.py:731` — `add_stat_value(stats, bonus_type, bonus_value)`
- `db_modules/dev_compat.py:975` — `def add_primary_stat_to_stats(stats, stat_key, value):`
- `db_modules/dev_compat.py:1078` — `add_primary_stat_to_stats(`
- `db_modules/dev_compat.py:1085` — `add_primary_stat_to_stats(`
- `db_modules/generated_equipment.py:163` — `def add_stat_value(stats, stat_key, value):`
- `db_modules/generated_equipment.py:237` — `add_stat_value(stats, main_stat, value)`
- `db_modules/generated_equipment.py:279` — `add_stat_value(stats, bonus, value)`
- `db_modules/generated_equipment.py:333` — `add_stat_value(stats, stat_choice, value)`
- `db_modules/generated_equipment.py:362` — `add_stat_value(stats, bonus_type, bonus_value)`
- `db_modules/generated_equipment.py:726` — `def add_primary_stat_to_stats(stats, stat_key, value):`
- `db_modules/generated_equipment.py:829` — `add_primary_stat_to_stats(`
- `db_modules/generated_equipment.py:836` — `add_primary_stat_to_stats(`
- `handlers/attribute_allocation.py:77` — `ATTRIBUTE_ALLOCATION_STATE: dict[int, dict] = {}`
- `handlers/attribute_allocation.py:134` — `if refresh or user_id not in ATTRIBUTE_ALLOCATION_STATE:`
- `handlers/attribute_allocation.py:137` — `ATTRIBUTE_ALLOCATION_STATE[user_id] = _new_draft(user_id)`
- `handlers/attribute_allocation.py:140` — `return ATTRIBUTE_ALLOCATION_STATE[user_id]`
- `handlers/attribute_allocation.py:155` — `ATTRIBUTE_ALLOCATION_STATE.pop(user_id, None)`
- `handlers/event_ui.py:35` — `for row in rows:kb.add(types.InlineKeyboardButton(f"{STATUS_LABELS[row['status']]} · {row['title']}",callback_data=PREFIX+f"{kind}:view:"+row["event_key"]))`
- `handlers/pvp_round_ui.py:30` — `kb.add(types.KeyboardButton(PVP_STATUS_BUTTON))`
- `systems/attribute_allocation_system.py:187` — `"""Atomically allocate points and return before/after state.`
- `systems/auction_house_system.py:2253` — `def _auction_add_stat_line(lines, label, value, prefix="+"):`
- `systems/auction_house_system.py:2338` — `_auction_add_stat_line(lines, "PDEF", _auction_snapshot_value(snapshot, "pdef", "physical_defense"))`
- `systems/auction_house_system.py:2339` — `_auction_add_stat_line(lines, "MDEF", _auction_snapshot_value(snapshot, "mdef", "magic_defense", "magical_defense"))`
- `systems/auction_house_system.py:2341` — `_auction_add_stat_line(lines, "STR", _auction_snapshot_value(snapshot, "bonus_str", "str", "strength"))`

### RESET

Evidence count: `115`

- `db_modules/dev_compat.py:3` — `# ROM 17.12.1.1 DEV RESET HERO LOCK INITIALIZATION`
- `db_modules/dev_compat.py:255` — `_DEV_RESET_HERO_LOCK = None`
- `db_modules/dev_compat.py:258` — `def _get_dev_reset_hero_lock():`
- `db_modules/dev_compat.py:259` — `global _DEV_RESET_HERO_LOCK`
- `db_modules/dev_compat.py:260` — `if _DEV_RESET_HERO_LOCK is None:`
- `db_modules/dev_compat.py:262` — `_DEV_RESET_HERO_LOCK = threading.RLock()`
- `db_modules/dev_compat.py:263` — `return _DEV_RESET_HERO_LOCK`
- `db_modules/dev_compat.py:265` — `def _dev_reset_table_exists(table_name):`
- `db_modules/dev_compat.py:272` — `def _dev_reset_table_columns(table_name):`
- `db_modules/dev_compat.py:273` — `if not _dev_reset_table_exists(table_name):`
- `db_modules/dev_compat.py:277` — `def _dev_reset_delete_by_user_columns(table_name, user_id, candidate_columns):`
- `db_modules/dev_compat.py:278` — `columns = _dev_reset_table_columns(table_name)`
- `db_modules/dev_compat.py:301` — `lock = _get_dev_reset_hero_lock()`
- `db_modules/dev_compat.py:334` — `if _dev_reset_table_exists("player_trades"):`
- `db_modules/dev_compat.py:350` — `columns = _dev_reset_table_columns(table_name)`
- `db_modules/dev_compat.py:388` — `count = _dev_reset_delete_by_user_columns(table_name, user_id, user_column_names)`
- `db_modules/dev_compat.py:393` — `if _dev_reset_table_exists("inventory_runes"):`
- `db_modules/dev_compat.py:399` — `if _dev_reset_table_exists("inventory_reservations"):`
- `db_modules/dev_compat.py:405` — `if _dev_reset_table_exists("equipment_slots"):`
- `db_modules/dev_compat.py:408` — `if _dev_reset_table_exists("inventory"):`
- `db_modules/dev_compat.py:422` — `"current_location": "start_path",  # ROM 18.23.3 DEV reset mirrors new-character start`
- `db_modules/dev_compat.py:448` — `user_columns = _dev_reset_table_columns("users")`
- `db_modules/dev_compat.py:475` — `"❌ DEV reset completed, але foreign_key_check виявив помилки. "`
- `db_modules/dev_compat.py:512` — `"message": f"❌ DEV reset error at {stage}: {error}",`
- `db_modules/dev_compat.py:517` — `"message": f"❌ DEV reset error: {last_error}",`
- `db_modules/quests.py:293` — `from .daily_compat import get_daily_quest_status, reset_daily_quest_if_needed as _reset_canonical_daily_quest_if_needed`
- `handlers/guild.py:145` — `def reset_guild_browse_state(user_id):`
- `handlers/guild.py:180` — `def reset_guild_create_state(user_id):`
- `handlers/guild.py:523` — `reset_guild_browse_state(user_id)`
- `handlers/guild.py:588` — `reset_guild_create_state(user_id)`

### FLOORS_AND_BOUNDS

Evidence count: `240`

- `data/defense_policy.py:10` — `return max(0.0, float(primary_stat or 0)) * DEFENSE_STAT_COEFFICIENT`
- `data/defense_policy.py:15` — `return max(0.0, float(item_defense or 0)) + calculate_stat_defense(primary_stat)`
- `data/defense_policy.py:20` — `return max(float(MINIMUM_DAMAGE), float(attack) - max(0.0, float(defense)) * DAMAGE_DEFENSE_COEFFICIENT)`
- `data/drop_tables.py:151` — `"elite": {"chance": None, "source": "min(1,mob.loot_chance+0.20)"},`
- `data/mana_policy.py:108` — `return min(maximum, amount)`
- `data/mana_policy.py:126` — `current = min(_non_negative_int(current_mp, "current_mp"), maximum)`
- `data/player_combat_chances.py:28` — `return max(float(minimum), min(float(maximum), float(value)))`
- `data/player_combat_chances.py:34` — `return CRIT_BASE_CHANCE + max(0.0, stat - CRIT_STAT_BASELINE) * CRIT_PER_STAT`
- `data/player_hp.py:13` — `safe_stamina = max(0, int(total_stamina or 0))`
- `data/priest_healing_policy.py:25` — `"heal": max(0, int(heal_per_turn)),`
- `data/stat_scaling.py:124` — `return max(0, round_stat(total))`
- `data/story_quest_definitions.py:47` — `"""Prerequisite item checked at interaction and optionally consumed."""`
- `data/story_quests/start_path_41_50.py:220` — `{'definition': {'quest_id': 'start_path_047_final_equipment_check',`
- `data/story_quests/start_path_41_50.py:262` — `'previous_quest_id': 'start_path_047_final_equipment_check',`
- `db_modules/dev_compat.py:112` — `return round(max(0.10, item_level * multiplier), 2)`
- `db_modules/dev_compat.py:287` — `return max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:356` — `deleted[table_name] = deleted.get(table_name, 0) + max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:361` — `deleted["player_trades"] = max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:398` — `deleted["inventory_runes"] = max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:404` — `deleted["inventory_reservations"] = deleted.get("inventory_reservations", 0) + max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:407` — `deleted["equipment_slots"] = max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:410` — `deleted["inventory"] = max(0, int(result.rowcount or 0))`
- `db_modules/dev_compat.py:1602` — `value = max(0, required - 1)`
- `db_modules/generated_equipment.py:140` — `return round(max(0.10, item_level * multiplier), 2)`
- `db_modules/generated_equipment.py:1055` — `class_aware_chance = max(0.0, min(1.0, class_aware_chance))`
- `db_modules/inventory.py:124` — `remaining = max(0, int(quantity) - max(0, int(free_space)))`
- `db_modules/inventory.py:167` — `free_space = sum(max(0, max_stack-int(row[1] or 0)) for row in partial)`
- `db_modules/inventory.py:181` — `current = max(0, int(current or 0))`
- `db_modules/inventory.py:182` — `moved = min(quantity, max_stack-current)`
- `db_modules/inventory.py:194` — `stack_quantity = min(quantity, max_stack)`

### READ_OWNERS

Evidence count: `240`

- `data/defense_policy.py:8` — `def calculate_stat_defense(primary_stat):`
- `data/defense_policy.py:13` — `def calculate_total_defense(item_defense, primary_stat):`
- `data/defense_policy.py:15` — `return max(0.0, float(item_defense or 0)) + calculate_stat_defense(primary_stat)`
- `data/equipment_identity_stat_policy.py:38` — `def get_identity_stat_weights(slot_key,*,item_subtype="",armor_type=""):`
- `data/equipment_identity_stat_policy.py:52` — `profile=get_identity_stat_weights(slot_key,item_subtype=item_subtype,armor_type=armor_type)`
- `data/equipment_stat_policy.py:122` — `def get_equipment_stat_weights(`
- `data/equipment_stat_policy.py:149` — `def get_allowed_equipment_stats(class_key: object, equipment_kind: str, *, item_subtype: str = "") -> tuple[str, ...]:`
- `data/equipment_stat_policy.py:150` — `return tuple(stat for stat, _weight in get_equipment_stat_weights(class_key, equipment_kind, item_subtype=item_subtype))`
- `data/equipment_stat_policy.py:169` — `profile = get_equipment_stat_weights(cls, kind)`
- `data/equipment_stat_policy.py:175` — `get_equipment_stat_weights(cls, "off_hand", item_subtype=subtype)`
- `data/equipment_stat_policy.py:178` — `if get_allowed_equipment_stats("knight", "off_hand", item_subtype="shield") != ("sta", "str"):`
- `data/equipment_stat_policy.py:191` — `profile = get_equipment_stat_weights(class_key, equipment_kind, item_subtype=item_subtype)`
- `data/equipment_stat_policy.py:224` — `"normalize_equipment_class", "get_equipment_stat_weights",`
- `data/equipment_stat_policy.py:225` — `"get_allowed_equipment_stats", "redistribute_primary_stat_budget",`
- `data/player_combat_chances.py:31` — `def _calculate_crit_chance_with_soft_cap(total_stat):`
- `data/runes.py:100` — `def get_rune_item_id(stat, level):`
- `data/stat_scaling.py:128` — `return _calculate_attack(class_key, stats, "patk", get_candidate(candidate_name))`
- `data/stat_scaling.py:132` — `return _calculate_attack(class_key, stats, "matk", get_candidate(candidate_name))`
- `data/stat_scaling.py:137` — `base_hp = calculate_base_max_hp(round_stat(level), round_stat(total_sta))`
- `data/story_quest_definitions.py:160` — `if player_level<unlock_level or not predecessor_completed or another_active_quest: return DerivedQuestStatus.LOCKED`
- `db.py:9` — `│   ├── player.py         - Player stats & progression`
- `db_modules/__init__.py:33` — `- player.py: Player stats, progression, HP (wrapper для player_system)`
- `db_modules/__init__.py:58` — `from .daily_compat import get_daily_quest_status`
- `db_modules/__init__.py:91` — `get_player_level, get_player_stats, get_user_progress, add_exp,`
- `db_modules/__init__.py:164` — `get_migration_status, run_db_startup_maintenance`
- `db_modules/__init__.py:217` — `'get_player_level', 'get_player_stats', 'get_user_progress', 'add_exp',`
- `db_modules/__init__.py:279` — `'get_migration_status', 'run_db_startup_maintenance',`
- `db_modules/__init__.py:366` — `'get_auction_house_stats', 'get_user_sellable_equipment_for_auction',`
- `db_modules/__init__.py:393` — `'get_auction_lot_market_price_stats',`
- `db_modules/__init__.py:406` — `'get_equipped_rune_stat_totals',`

### WRITE_OWNERS

Evidence count: `134`

- `handlers/guild.py:145` — `def reset_guild_browse_state(user_id):`
- `handlers/guild.py:180` — `def reset_guild_create_state(user_id):`
- `handlers/guild.py:523` — `reset_guild_browse_state(user_id)`
- `handlers/guild.py:588` — `reset_guild_create_state(user_id)`
- `handlers/guild.py:638` — `reset_guild_create_state(user_id)`
- `handlers/guild.py:709` — `reset_guild_browse_state(message.from_user.id)`
- `handlers/guild.py:713` — `reset_guild_browse_state(message.from_user.id)`
- `handlers/guild.py:717` — `reset_guild_browse_state(message.from_user.id)`
- `handlers/guild.py:726` — `reset_guild_create_state(message.from_user.id)`
- `handlers/guild.py:727` — `reset_guild_browse_state(message.from_user.id)`
- `handlers/guild.py:732` — `reset_guild_create_state(message.from_user.id)`
- `handlers/guild.py:733` — `reset_guild_browse_state(message.from_user.id)`
- `handlers/guild.py:876` — `def reset_guild_application_review_state(user_id):`
- `handlers/guild.py:1069` — `reset_guild_application_review_state(user_id)`
- `handlers/guild.py:1115` — `reset_guild_application_review_state(message.from_user.id)`
- `handlers/guild.py:1166` — `def reset_guild_member_manage_state(user_id):`
- `handlers/guild.py:1384` — `reset_guild_member_manage_state(user_id)`
- `handlers/guild.py:1477` — `def _guild_safe_reset_other_states_for_members_v2(user_id):`
- `handlers/guild.py:1479` — `reset_guild_browse_state(user_id)`
- `handlers/guild.py:1483` — `reset_guild_application_review_state(user_id)`
- `handlers/guild.py:1665` — `_guild_safe_reset_other_states_for_members_v2(user_id)`
- `handlers/guild.py:1702` — `reset_guild_member_manage_state(user_id)`
- `handlers/guild.py:1789` — `reset_guild_application_review_state(user_id)`
- `handlers/guild.py:2063` — `def _guild_progress_reset_navigation_states_v1(user_id):`
- `handlers/guild.py:2065` — `"reset_guild_browse_state",`
- `handlers/guild.py:2066` — `"reset_guild_application_review_state",`
- `handlers/guild.py:2067` — `"reset_guild_member_manage_state",`
- `handlers/guild.py:2138` — `_guild_progress_reset_navigation_states_v1(user_id)`
- `handlers/guild.py:2143` — `_guild_progress_reset_navigation_states_v1(user_id)`
- `handlers/guild.py:2148` — `_guild_progress_reset_navigation_states_v1(user_id)`

## Decision

Conclusion: `GO`

The audit report is the only allowed input for `patch_21_6_4a_implement_primary_stats.py`. The mutation must not add class initial stats, allocation rates, floors, reset rules, formulas, or storage semantics that are not explicitly supported by this audit evidence.

## Manual game check

Not required. This patch is static and read-only.
