# Stage 21.6.X1 — Account and character V1 parity audit

## Scope

Read-only post-implementation audit of Stages 21.6.1 and 21.6.2 against tracked V1 production sources. V1 modules were not imported or executed and no database was opened.

## Decision model

The audit deliberately does not treat a text match as final semantic proof. Every implemented claim is classified for review. Missing or ambiguous V1 evidence blocks progression until a reconciliation decision is recorded.

## Findings

### ACCOUNT_TELEGRAM_IDENTITY

- stage: `21.6.1`
- V2 claim: Telegram identity is the stable unique account identity.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `config.py:16` — `raw = str(os.getenv("ROM_ADMIN_USER_IDS", "")).strip()`
- `config.py:19` — `ROM_ADMIN_USER_IDS = _admin_ids_env()`
- `data/story_quest_item_identity.py:8` — `STORY_QUEST_ITEM_IDENTITY_COLUMNS = ("user_id", "quest_id", "item_key")`
- `data/story_quest_item_identity.py:10` — `{"id", "user_id", "quest_id", "item_key", "quantity", "updated_at"}`
- `data/story_quest_item_identity.py:71` — `errors.append("missing UNIQUE(user_id, quest_id, item_key)")`
- `db.py:27` — `user = db.get_user(user_id)`
- `db.py:28` — `db.add_item(user_id, item_id, quantity)`
- `db.py:29` — `db.create_guild(user_id, name, tag)`
- `db_modules/__init__.py:344` — `'get_guild_member', 'get_character_name_by_user_id',`
- `db_modules/character.py:38` — `def get_character_name(user_id):`
- `db_modules/character.py:39` — `return _character_system().get_character_name(user_id)`
- `db_modules/character.py:42` — `def set_character_name(user_id, name):`

### ACCOUNT_REGISTERED_AT_UTC

- stage: `21.6.1`
- V2 claim: Registration timestamp is preserved in canonical UTC.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `db_modules/connection.py:62` — `registered_at TEXT DEFAULT ''`
- `db_modules/connection.py:150` — `("users", "registered_at", "TEXT DEFAULT ''"),`
- `db_modules/player.py:143` — `registered_at = datetime.now(timezone.utc).isoformat()`
- `db_modules/player.py:166` — `registered_at`
- `db_modules/player.py:189` — `registered_at`
- `db_modules/story_quests.py:23` — `def utc_now_iso() -> str:`
- `db_modules/story_quests.py:24` — `"""Return a timezone-aware UTC ISO-8601 timestamp for persistent storage."""`
- `db_modules/story_quests.py:25` — `return datetime.now(timezone.utc).isoformat()`
- `db_modules/story_quests.py:92` — `now = str(timestamp or utc_now_iso())`
- `db_modules/story_quests.py:134` — `(bounded, str(timestamp or utc_now_iso()), int(user_id), str(quest_id)),`
- `db_modules/story_quests.py:197` — `(take, utc_now_iso(), int(user_id), str(quest_id), str(item_key), current),`
- `db_modules/story_quests.py:242` — `str(timestamp or utc_now_iso())),`

### ACCOUNT_STATUS_LIFECYCLE

- stage: `21.6.1`
- V2 claim: Account statuses active/blocked/closed and terminal close transition exist.
- classification: `AMBIGUOUS_V1_EVIDENCE_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `data/story_quest_definitions.py:157` — `def derive_story_quest_status(*,persistent_status,player_level,unlock_level,predecessor_completed,another_active_quest):`
- `db_modules/quests.py:24` — `status TEXT DEFAULT 'active',`
- `db_modules/quests.py:71` — `"status": "active",`
- `db_modules/quests.py:113` — `if quest["status"] != "active":`
- `db_modules/quests.py:265` — `("trades_completed", 0), ("status", "active"), ("claimed_at", None),`
- `db_modules/story_quests.py:12` — `VALID_PERSISTENT_STATUSES = frozenset({"ACTIVE", "COMPLETED", "SKIPPED"})`
- `db_modules/story_quests.py:56` — `"SELECT * FROM user_story_quests WHERE user_id=? AND status='ACTIVE'",`
- `db_modules/story_quests.py:95` — `if existing["status"] == "ACTIVE":`
- `db_modules/story_quests.py:125` — `if row is None or row["status"] != "ACTIVE":`
- `db_modules/story_quests.py:133` — `WHERE user_id=? AND quest_id=? AND status='ACTIVE'""",`
- `db_modules/story_quests.py:228` — `if quest is None or quest["status"] != "ACTIVE":`
- `db_modules/story_quests.py:279` — `WHERE user_id=? AND quest_id=? AND status='ACTIVE'""",`

### ACCOUNT_BAG_CAPACITY

- stage: `21.6.1`
- V2 claim: Bag capacity is account-level and survives character reset.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `db_modules/__init__.py:146` — `get_bag_capacity, get_inventory_used_slots,`
- `db_modules/__init__.py:263` — `'get_bag_capacity', 'get_inventory_used_slots',`
- `db_modules/connection.py:20` — `DEFAULT_BAG_SLOTS = 60  # ROM 17.8.1 BASE BAG CAPACITY 60`
- `db_modules/dev_compat.py:33` — `def get_bag_capacity(user_id):`
- `db_modules/dev_compat.py:49` — `return max(DEFAULT_BAG_SLOTS, capacity)`
- `db_modules/dev_compat.py:421` — `"bag_slots": max(int(globals().get("DEFAULT_BAG_SLOTS", 60)), int(get_bag_capacity(user_id))),  # ROM 17.32.1 preserve account entitlement`
- `db_modules/dev_compat.py:1240` — `capacity = get_bag_capacity(user_id)`
- `db_modules/dev_compat.py:1420` — `capacity = get_bag_capacity(user_id)`
- `db_modules/generated_equipment.py:55` — `def get_bag_capacity(user_id):`
- `db_modules/generated_equipment.py:71` — `return max(DEFAULT_BAG_SLOTS, capacity)`
- `db_modules/generated_equipment.py:382` — `capacity = get_bag_capacity(user_id)`
- `db_modules/generated_equipment.py:1040` — `capacity = get_bag_capacity(user_id)`

### ACCOUNT_CRYSTAL_WALLET

- stage: `21.6.1`
- V2 claim: Crystal wallet is account-level and initialized with zero balance.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `data/about_game.py:5` — `ABOUT_GAME_SECTION_ORDER=("world","classes","progression","combat","items","runes","guilds","crystals","tips")`
- `data/about_game.py:76` — `"crystals":{"button":"💎 Кристали","title":"💎 Кристали","text":'''Кристали є окремою валютою акаунта. Вони зберігаються незалежно від поточного персонажа та не зникають після звичайного скидання прогресу героя.`
- `db_modules/__init__.py:18` — `from systems.crystal_wallet_system import (`
- `db_modules/__init__.py:19` — `init_crystal_wallet_system,`
- `db_modules/__init__.py:20` — `get_crystal_wallet,`
- `db_modules/__init__.py:21` — `get_crystal_balance,`
- `db_modules/__init__.py:22` — `credit_crystals,`
- `db_modules/__init__.py:23` — `debit_crystals,`
- `db_modules/__init__.py:501` — `__all__.extend(['init_crystal_wallet_system','get_crystal_wallet','get_crystal_balance','credit_crystals','debit_crystals','get_crystal_transactions','compensate_crystal_transaction'])`
- `db_modules/dev_compat.py:378` — `protected_tables = {"users", "items", "inventory", "equipment_slots", "inventory_runes", "crystal_wallets", "crystal_transactions"}`
- `handlers/admin_crystal_credit.py:10` — `states={};COMMAND='/admin_crystals'`
- `handlers/admin_crystal_credit.py:57` — `@bot.message_handler(commands=['admin_crystals'])`

### ACCOUNT_REGISTER_IDEMPOTENCY

- stage: `21.6.1`
- V2 claim: Repeated registration/start returns the same account without rewriting registration identity.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `db_modules/connection.py:62` — `registered_at TEXT DEFAULT ''`
- `db_modules/connection.py:150` — `("users", "registered_at", "TEXT DEFAULT ''"),`
- `db_modules/connection.py:224` — `ON CONFLICT(id) DO UPDATE SET`
- `db_modules/dev_compat.py:146` — `"message": "❌ Персонажа не знайдено. Спочатку натисни /start."`
- `db_modules/dev_compat.py:238` — `"message": "❌ Персонажа не знайдено. Спочатку натисни /start."`
- `db_modules/dev_compat.py:327` — `"message": "❌ Персонажа не знайдено. Спочатку натисни /start.",`
- `db_modules/dev_compat.py:763` — `ON CONFLICT(id) DO UPDATE SET`
- `db_modules/inventory_compat.py:271` — `ON CONFLICT(id) DO UPDATE SET`
- `db_modules/migrations.py:70` — `ON CONFLICT(id) DO UPDATE SET`
- `db_modules/player.py:143` — `registered_at = datetime.now(timezone.utc).isoformat()`
- `db_modules/player.py:146` — `INSERT OR IGNORE INTO users (`
- `db_modules/player.py:166` — `registered_at`

### ACCOUNT_OPTIMISTIC_VERSION

- stage: `21.6.1`
- V2 claim: Account mutation uses optimistic version checks.
- classification: `V2_SAFEGUARD_REVIEW_REQUIRED`
- V1 evidence count: `0`


### CHARACTER_SINGLE_PER_ACCOUNT

- stage: `21.6.2`
- V2 claim: One character exists per account.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `data/story_quest_item_identity.py:71` — `errors.append("missing UNIQUE(user_id, quest_id, item_key)")`
- `db_modules/__init__.py:104` — `init_character_class_system,`
- `db_modules/__init__.py:105` — `normalize_character_name, validate_character_name,`
- `db_modules/__init__.py:106` — `get_character_name, set_character_name, is_character_name_taken,`
- `db_modules/__init__.py:107` — `needs_character_name, needs_character_class,`
- `db_modules/__init__.py:108` — `get_character_class, set_character_class, get_character_class_display,`
- `db_modules/__init__.py:228` — `'init_character_class_system',`
- `db_modules/__init__.py:229` — `'normalize_character_name', 'validate_character_name',`
- `db_modules/__init__.py:230` — `'get_character_name', 'set_character_name', 'is_character_name_taken',`
- `db_modules/__init__.py:231` — `'needs_character_name', 'needs_character_class',`
- `db_modules/__init__.py:232` — `'get_character_class', 'set_character_class', 'get_character_class_display',`
- `db_modules/__init__.py:344` — `'get_guild_member', 'get_character_name_by_user_id',`

### CHARACTER_NAME_RULES

- stage: `21.6.2`
- V2 claim: Name length is 1-64, exact whitespace is forbidden, and control characters are forbidden.
- classification: `AMBIGUOUS_V1_EVIDENCE_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `config.py:9` — `raw = str(os.getenv(name, default)).strip()`
- `config.py:16` — `raw = str(os.getenv("ROM_ADMIN_USER_IDS", "")).strip()`
- `config.py:17` — `return frozenset(int(part.strip()) for part in raw.split(",") if part.strip())`
- `config.py:29` — `_GAME_CHAT_URL_RAW = str(os.getenv("GAME_CHAT_URL", "") or "").strip()`
- `config.py:30` — `_NEWS_CHANNEL_URL_RAW = str(os.getenv("NEWS_CHANNEL_URL", "") or "").strip()`
- `config.py:31` — `_SUPPORT_URL_RAW = str(os.getenv("SUPPORT_URL", "") or "").strip()`
- `config.py:35` — `value = str(value or "").strip()`
- `data/equipment_identity_stat_policy.py:59` — `selected=str(chooser(profile)).strip().lower()`
- `data/equipment_stat_policy.py:94` — `key = str(class_key or "").strip().lower()`
- `data/equipment_stat_policy.py:130` — `kind = str(equipment_kind or "").strip().lower()`
- `data/equipment_stat_policy.py:131` — `subtype = str(item_subtype or "").strip().lower()`
- `data/equipment_stat_policy.py:204` — `selected = str(chooser(profile) or "").strip().lower()`

### CHARACTER_NAME_UNIQUENESS

- stage: `21.6.2`
- V2 claim: Character names are globally unique.
- classification: `AMBIGUOUS_V1_EVIDENCE_REVIEW_REQUIRED`
- V1 evidence count: `7`

- `systems/character_system.py:185` — `return {"success": False, "message": "❌ Це ім’я вже зайняте іншим персонажем."}`
- `systems/name_rune_system.py:28` — `c.executescript("""CREATE TABLE IF NOT EXISTS character_name_changes(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,old_name TEXT NOT NULL,new_name TEXT NOT NULL,normalized_new_name TEXT NOT NULL,inventory_id INTEGER NOT NULL,item_id INTEGER NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_character_name_`
- `systems/name_rune_system.py:45` — `if normalize_name(other['character_name']).casefold()==v['key']:return {'success':False,'message':'Це ім’я вже зайняте.'}`
- `systems/name_rune_system.py:64` — `if normalize_name(other[0]).casefold()==v['key']:c.rollback();return {'success':False,'message':'Це ім’я вже зайняте.'}`
- `tools/audit_guild_contract_target_log.py:87` — `"Guild formatter ignores target_mob_name and falls back to 'контракт'. The Contract System already snapshots the full contract before deletion and passes it to the Guild hook."`
- `tools/smoke_test_character_mutation_contracts.py:76` — `if cs.is_character_name_taken(generated_name,exclude_user_id=TEST_USER_ID): fail("exclude_user_id uniqueness contract failed")`
- `tools/verify_stage_19_31_2_quest_71_spoiler.py:7` — `assert q['acceptance_text']=='Ми зіставили сім зарубок на жетоні з відомими стежками. Шість маршрутів ведуть до стоянок, які розвідники вже бачили. Остання стежка проходить через стару вирубку й зникає біля кам’яного яру.\n\nУночі над деревами в тому напрямку видно червоне світло, а вітер приносить запах диму. До яру регулярно прямують озброєні гобліни.\n\nЦе перший маршрут, який не збігається з жодною відомою стоянкою. Отже, за кам’яним яром прихована частина мережі, якої ще немає на наших карт`

### CHARACTER_CLASS_KEY

- stage: `21.6.2`
- V2 claim: Character persists one stable technical class key.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `data/equipment_stat_policy.py:93` — `def normalize_equipment_class(class_key: object) -> str:`
- `data/equipment_stat_policy.py:94` — `key = str(class_key or "").strip().lower()`
- `data/equipment_stat_policy.py:96` — `raise ValueError(f"Unsupported equipment target class: {class_key!r}")`
- `data/equipment_stat_policy.py:123` — `class_key: object,`
- `data/equipment_stat_policy.py:129` — `cls = normalize_equipment_class(class_key)`
- `data/equipment_stat_policy.py:149` — `def get_allowed_equipment_stats(class_key: object, equipment_kind: str, *, item_subtype: str = "") -> tuple[str, ...]:`
- `data/equipment_stat_policy.py:150` — `return tuple(stat for stat, _weight in get_equipment_stat_weights(class_key, equipment_kind, item_subtype=item_subtype))`
- `data/equipment_stat_policy.py:183` — `def redistribute_primary_stat_budget(stats, class_key, equipment_kind, *, item_subtype="", chooser):`
- `data/equipment_stat_policy.py:191` — `profile = get_equipment_stat_weights(class_key, equipment_kind, item_subtype=item_subtype)`
- `data/stat_scaling.py:50` — `class_key: MappingProxyType({`
- `data/stat_scaling.py:54` — `for class_key in SUPPORTED_CLASSES`
- `data/stat_scaling.py:62` — `def normalize_class_key(value: object) -> str:`

### CHARACTER_START_LOCATION

- stage: `21.6.2`
- V2 claim: Canonical initial and reset location is start_path.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `data/bosses.py:24` — `"location_id": "start_path",`
- `data/location_graph.py:7` — `"start_path": {"id": "start_path", "name": "🌿 Початок Шляху", "kind": "location", "huntable": True},`
- `data/location_graph.py:12` — `"city": ("start_path",),`
- `data/location_graph.py:13` — `"start_path": ("city", "dark_forest"),`
- `data/location_graph.py:14` — `"dark_forest": ("start_path",),`
- `data/locations.py:2` — `"start_path": {`
- `data/locations.py:3` — `"id": "start_path",`
- `data/locations.py:61` — `"start_path",`
- `data/locations.py:67` — `return LOCATIONS.get(location_id, LOCATIONS["start_path"])`
- `data/mobs.py:5` — `START_PATH_MOBS = [`
- `data/mobs.py:11` — `"location_id": "start_path",`
- `data/mobs.py:39` — `"location_id": "start_path",`

### CHARACTER_CURRENT_RESOURCES

- stage: `21.6.2`
- V2 claim: Current HP and MP are persisted character state and non-negative.
- classification: `V1_EVIDENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `80`

- `data/mana_policy.py:120` — `current_mp: Any,`
- `data/mana_policy.py:126` — `current = min(_non_negative_int(current_mp, "current_mp"), maximum)`
- `db_modules/__init__.py:54` — `from .equipment import check_armor_compatibility_for_class, check_main_hand_compatibility_for_class, check_off_hand_compatibility_for_class, check_two_handed_conflict_for_equip`
- `db_modules/__init__.py:96` — `get_max_hp, get_current_hp_raw, get_current_hp, set_current_hp,`
- `db_modules/__init__.py:222` — `'get_max_hp', 'get_current_hp_raw', 'get_current_hp', 'set_current_hp',`
- `db_modules/__init__.py:493` — `__all__.extend(['check_armor_compatibility_for_class', 'check_main_hand_compatibility_for_class', 'check_off_hand_compatibility_for_class', 'check_two_handed_conflict_for_equip'])`
- `db_modules/character.py:136` — `current_mp = mp_data.get("mp", 0)`
- `db_modules/character.py:147` — `"mp": current_mp,`
- `db_modules/character.py:151` — `if current_mp < amount:`
- `db_modules/character.py:157` — `f"🔵 У тебе: {current_mp}/{max_mp} MP"`
- `db_modules/character.py:159` — `"mp": current_mp,`
- `db_modules/character.py:163` — `new_mp = current_mp - amount`

### CHARACTER_RESET_SEMANTICS

- stage: `21.6.2`
- V2 claim: Reset preserves character ID, account, name, and class while resetting level, EXP, location, HP, and MP.
- classification: `AMBIGUOUS_V1_EVIDENCE_REVIEW_REQUIRED`
- V1 evidence count: `61`

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

### CHARACTER_OPTIMISTIC_VERSION

- stage: `21.6.2`
- V2 claim: Character reset uses optimistic version checks.
- classification: `V1_REFERENCE_FOUND_REVIEW_REQUIRED`
- V1 evidence count: `1`

- `systems/simulation/economic_ledger.py:80` — `character_class:str; profile:str; seed:int; target_level:int; inventory_capacity:int; max_days:int=365; schema_version:str=SCHEMA_VERSION; ledger_version:str=LEDGER_VERSION`

## Audit conclusion

`REVIEW_REQUIRED`

## Required next action

Review every claim against the captured V1 line evidence. If any Stage 21.6.1 or 21.6.2 behavior is absent, broader, or contradictory in V1, create `patch_21_6_X1a_reconcile_account_character_parity.py` before Stage 21.6.4. Do not mutate production from this audit.

## Manual game check

Not required for this static read-only audit.
