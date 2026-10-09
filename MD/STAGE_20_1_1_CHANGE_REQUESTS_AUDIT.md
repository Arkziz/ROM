# Stage 20.1.1 — аудит усіх запитів Stage 20

- Статус: **PASS**
- Рішення: **GO**
- Час: `2026-10-09T21:27:27+03:00`
- Git branch: `develop`
- Git HEAD: `4f79f81499fcdbffae7583e2e286a05978cde16d`

## Гарантії виконання

- Production-файли не змінювалися.
- `game.db` відкривався лише через SQLite URI `mode=ro`, якщо база була присутня.
- `game.db-wal` і `game.db-shm` не видалялися, не очищалися, не копіювалися і не перейменовувалися.
- Створено лише звіти у `reports/` та `MD/`.

## Попередні ключові висновки

### FIRIUS_RUNTIME_SPLIT
- Рівень: **HIGH**
- У коді присутні окремі quantity-константи для potion reward і Firius token reward.
- Наступний підетап: `20.4.1`

### EQUIPMENT_PROBABILISTIC_CLASS_AWARE
- Рівень: **HIGH**
- Central drop містить class_aware_chance, тому off-class stat може бути наслідком policy, а не генераторної помилки.
- Наступний підетап: `20.6.3`

### BASIC_ATTACK_DEFAULT_PHYSICAL_REVIEW
- Рівень: **HIGH**
- calculate_player_attack/default attack_type та handler dispatch потребують окремого parity-аудиту перед mutation.
- Наступний підетап: `20.2.1`

### PRIEST_HEAL_LITERAL_REVIEW
- Рівень: **HIGH**
- Поточні duration/cooldown і presentation literals мають бути консолідовані через lifecycle audit.
- Наступний підетап: `20.2.4`

## Домени

### Щоденне завдання та Жетони Фіріуса
- Статус: **PASS**
- Зафіксоване рішення: Нагорода за щоденне завдання: 3 Жетони Фіріуса; без ретроактивного вилучення.
- Файлів із збігами: 11
- Очікувані owners:
  - `data/runes.py`: exists=True, hits=True
  - `data/balance.py`: exists=True, hits=True
  - `systems/rune_system.py`: exists=True, hits=True
  - `handlers/daily.py`: exists=True, hits=True
- Основні call sites:
  - `data/balance.py:21` — `DAILY_QUEST_REWARD_ITEM_ID = 401`
  - `data/balance.py:22` — `DAILY_QUEST_REWARD_QUANTITY = 3`
  - `data/balance.py:43` — `'DAILY_QUEST_REWARD_ITEM_ID',`
  - `data/balance.py:44` — `'DAILY_QUEST_REWARD_QUANTITY',`
  - `data/runes.py:31` — `FIRIUS_TOKENS_PER_DAILY_REWARD = 5`
  - `data/runes.py:61` — `"name": "🪙 Жетон Фіріуса",`
  - `db_modules/__init__.py:184` — `is_daily_quest_complete, claim_daily_quest_reward,`
  - `db_modules/__init__.py:295` — `'is_daily_quest_complete', 'claim_daily_quest_reward',`
  - `db_modules/__init__.py:415` — `'get_firius_token_quantity',`
  - `db_modules/daily_compat.py:11` — `DAILY_QUEST_REWARD_ITEM_ID,`
  - `db_modules/daily_compat.py:12` — `DAILY_QUEST_REWARD_QUANTITY,`
  - `db_modules/daily_compat.py:151` — `"reward_item_id": DAILY_QUEST_REWARD_ITEM_ID,`
  - `db_modules/daily_compat.py:152` — `"reward_quantity": DAILY_QUEST_REWARD_QUANTITY`
  - `db_modules/quests.py:122` — `def claim_daily_quest_reward(user_id):`
  - `db_modules/quests.py:125` — `from data.balance import DAILY_QUEST_REWARDS`
  - `db_modules/quests.py:147` — `for item_id, quantity in DAILY_QUEST_REWARDS.get("items", []):`
  - `db_modules/quests.py:158` — `gold_amount = float(DAILY_QUEST_REWARDS.get("gold", 0) or 0)`
  - `db_modules/quests.py:167` — `if "items" in DAILY_QUEST_REWARDS:`
  - `db_modules/systems_wrappers.py:652` — `def claim_daily_quest_reward(user_id):`
  - `db_modules/systems_wrappers.py:653` — `return _rune_system().claim_daily_quest_reward_with_firius_tokens(user_id)`

### Тип звичайної атаки за класом
- Статус: **PASS**
- Зафіксоване рішення: Mage/Priest: MATK проти MDEF, cost 0; physical classes: PATK проти PDEF.
- Файлів із збігами: 34
- Очікувані owners:
  - `handlers/combat.py`: exists=True, hits=True
  - `systems/combat_system.py`: exists=True, hits=True
  - `systems/pvp_round_engine.py`: exists=True, hits=True
  - `systems/pvp_skill_adapter.py`: exists=True, hits=False
- Основні call sites:
  - `data/bosses.py:27` — `"attack_type": "physical",`
  - `data/bosses.py:42` — `"attack_type": "physical",`
  - `data/bosses.py:46` — `"attack_type": "physical", "bleed_turns": 2,`
  - `data/bosses.py:52` — `"attack_type": "magical",`
  - `data/bosses.py:56` — `"attack_type": "physical", "once_per_fight": True,`
  - `data/bosses.py:72` — `"attack_type": "physical",`
  - `data/bosses.py:89` — `"attack_type": "physical",`
  - `data/bosses.py:93` — `"attack_type": "physical",`
  - `data/bosses.py:107` — `"attack_type": "physical", "once_per_fight": True,`
  - `data/equipment_profiles.py:26` — `"attack_type": "physical",`
  - `data/equipment_profiles.py:40` — `"attack_type": "physical",`
  - `data/equipment_profiles.py:54` — `"attack_type": "magical",`
  - `data/equipment_profiles.py:68` — `"attack_type": "physical",`
  - `data/equipment_profiles.py:82` — `"attack_type": "magical",`
  - `data/equipment_profiles.py:96` — `"attack_type": "physical",`
  - `data/equipment_profiles.py:110` — `"attack_type": "physical",`
  - `data/equipment_profiles.py:126` — `"attack_type": "defense",`
  - `data/equipment_profiles.py:134` — `"attack_type": "defense",`
  - `data/equipment_profiles.py:146` — `"attack_type": "magical",`
  - `data/equipment_profiles.py:158` — `"attack_type": "physical",`

### Благословення зцілення Жреця
- Статус: **PASS**
- Зафіксоване рішення: duration=2 ходи; cooldown=4 ходи; замінює попереднє mana-ТЗ.
- Файлів із збігами: 6
- Очікувані owners:
  - `handlers/combat.py`: exists=True, hits=True
  - `systems/pvp_skill_adapter.py`: exists=True, hits=False
  - `systems/pvp_round_engine.py`: exists=True, hits=False
  - `systems/simulation/skill_catalog.py`: exists=True, hits=False
- Основні call sites:
  - `handlers/combat.py:717` — `def init_skill_cooldowns(mob):`
  - `handlers/combat.py:718` — `if "skill_cooldowns" not in mob:`
  - `handlers/combat.py:719` — `mob["skill_cooldowns"] = {}`
  - `handlers/combat.py:722` — `def get_skill_cooldown(mob, skill_key):`
  - `handlers/combat.py:723` — `init_skill_cooldowns(mob)`
  - `handlers/combat.py:725` — `return int(mob["skill_cooldowns"].get(skill_key, 0) or 0)`
  - `handlers/combat.py:728` — `def set_skill_cooldown(mob, skill_key, cooldown_turns):`
  - `handlers/combat.py:730` — `init_skill_cooldowns(mob)`
  - `handlers/combat.py:734` — `mob["skill_cooldowns"].pop(skill_key, None)`
  - `handlers/combat.py:737` — `mob["skill_cooldowns"][skill_key] = cooldown_turns + 1`
  - `handlers/combat.py:742` — `def tick_skill_cooldowns_at_player_turn(mob):`
  - `handlers/combat.py:743` — `init_skill_cooldowns(mob)`
  - `handlers/combat.py:745` — `if not mob["skill_cooldowns"]:`
  - `handlers/combat.py:750` — `for skill_key in list(mob["skill_cooldowns"].keys()):`
  - `handlers/combat.py:751` — `old_value = int(mob["skill_cooldowns"].get(skill_key, 0) or 0)`
  - `handlers/combat.py:756` — `del mob["skill_cooldowns"][skill_key]`
  - `handlers/combat.py:758` — `mob["skill_cooldowns"][skill_key] = new_value`
  - `handlers/combat.py:768` — `def validate_skill_cooldown(mob, skill):`
  - `handlers/combat.py:770` — `cooldown = get_skill_cooldown(mob, skill_key)`
  - `handlers/combat.py:1029` — `"key": "priest_healing_blessing",`

### Mana pipeline
- Статус: **PASS**
- Зафіксоване рішення: Hybrid mana costs і 50% post-combat floor реалізуються окремо у Stage 20.3.
- Файлів із збігами: 39
- Очікувані owners:
  - `systems/regen_system.py`: exists=True, hits=True
  - `systems/stat_system.py`: exists=True, hits=True
  - `handlers/combat.py`: exists=True, hits=True
  - `systems/pvp_round_engine.py`: exists=True, hits=True
  - `systems/simulation/skill_catalog.py`: exists=True, hits=False
- Основні call sites:
  - `data/classes.py:48` — `"resource": "mana",`
  - `data/classes.py:57` — `"resource": "mana",`
  - `data/stat_system_config.py:27` — `MAX_MP_SCALING = {`
  - `data/stat_system_config.py:53` — `if set(MAX_MP_SCALING) != {"base", "level", "int", "wis"}:`
  - `data/stat_system_config.py:54` — `problems.append("MAX_MP_SCALING: key mismatch")`
  - `data/stat_system_config.py:55` — `for key, value in MAX_MP_SCALING.items():`
  - `data/stat_system_config.py:57` — `problems.append(f"MAX_MP_SCALING/{key}: coefficient must be numeric")`
  - `data/stat_system_config.py:59` — `problems.append(f"MAX_MP_SCALING/{key}: coefficient must be finite and non-negative")`
  - `db_modules/__init__.py:110` — `get_user_mp, set_user_mp, spend_user_mp, restore_user_mp_to_full,`
  - `db_modules/__init__.py:111` — `get_max_mp, refresh_user_mp,`
  - `db_modules/__init__.py:234` — `'get_user_mp', 'set_user_mp', 'spend_user_mp', 'restore_user_mp_to_full',`
  - `db_modules/__init__.py:235` — `'get_max_mp', 'refresh_user_mp',`
  - `db_modules/character.py:136` — `current_mp = mp_data.get("mp", 0)`
  - `db_modules/character.py:137` — `max_mp = mp_data.get("max_mp", 0)`
  - `db_modules/character.py:147` — `"mp": current_mp,`
  - `db_modules/character.py:148` — `"max_mp": max_mp`
  - `db_modules/character.py:151` — `if current_mp < amount:`
  - `db_modules/character.py:157` — `f"🔵 У тебе: {current_mp}/{max_mp} MP"`
  - `db_modules/character.py:159` — `"mp": current_mp,`
  - `db_modules/character.py:160` — `"max_mp": max_mp`

### Золото за підняття рівня
- Статус: **PASS**
- Зафіксоване рішення: Конкретні значення визначаються тільки після Stage 20.1.2.
- Файлів із збігами: 18
- Очікувані owners:
  - `systems/level_up_reward_system.py`: exists=True, hits=True
  - `data/player_progression.py`: exists=True, hits=True
- Основні call sites:
  - `data/player_progression.py:60` — `level_ups = 0`
  - `data/player_progression.py:73` — `level_ups += 1`
  - `data/player_progression.py:74` — `return {"level": level, "exp": exp, "exp_to_next": get_exp_to_next_level(level), "level_ups": level_ups, "unapplied_exp": amount}`
  - `db_modules/dev_compat.py:1586` — `__all__ = ['set_player_level_for_test', 'reset_player_level_for_test', 'set_gold_for_test', 'create_dev_armor_item_for_test', 'create_dev_weapon_item_for_test', 'reset_hero_for_test', 'seed_class_reset_sphere_item']`
  - `handlers/city.py:284` — `kb.add(types.InlineKeyboardButton(text=f"{offer['slot_name']} — {format_gold(offer['price'])} (рівень {offer['item_level']})", callback_data=callback_data))`
  - `handlers/city.py:308` — `kb.add(types.InlineKeyboardButton(text=f"{offer['name']}{hands_text} — {format_gold(offer['price'])} (рівень {offer['item_level']})", callback_data=f"buy_common_equipment:{slot_key}:{offer['profile_key']}"))`
  - `handlers/combat.py:2042` — `reward_message = str(exp_result.get("level_up_reward_message") or "").strip()`
  - `handlers/combat.py:2043` — `level_ups = int(exp_result.get("level_ups", 0) or 0)`
  - `handlers/combat.py:2044` — `if level_ups > 0 and not reward_message:`
  - `handlers/combat.py:2047` — `old_level = int(exp_result.get("old_level", resulting_level - level_ups) or 0)`
  - `handlers/combat.py:2049` — `points = int(exp_result.get("attribute_points_awarded", level_ups * 5) or 0)`
  - `handlers/contracts.py:284` — `reward_message = str(result.get("level_up_reward_message") or "")`
  - `handlers/world_chronicles.py:64` — `elif event_type == "player_level_up":`
  - `systems/contract_system.py:545` — `"level_up_reward_message": (`
  - `systems/contract_system.py:546` — `str(exp_result.get("level_up_reward_message") or "") if exp_result else ""`
  - `systems/guild_system.py:2243` — `event_type="guild_level_up",`
  - `systems/level_up_reward_system.py:43` — `"gold": level * (12 if milestone else 8),`
  - `systems/level_up_reward_system.py:115` — `def init_level_up_reward_system(db):`
  - `systems/level_up_reward_system.py:119` — `CREATE TABLE IF NOT EXISTS level_up_rewards (`
  - `systems/level_up_reward_system.py:157` — `columns = _table_columns(db, "level_up_rewards")`

### Ціни зіль і створення гільдії
- Статус: **PASS**
- Зафіксоване рішення: Ціни не змінюються до економічних аудитів 20.4.3 і 20.4.5.
- Файлів із збігами: 52
- Очікувані owners:
  - `systems/potion_system.py`: exists=True, hits=True
  - `handlers/city.py`: exists=True, hits=True
  - `systems/guild_system.py`: exists=True, hits=True
  - `handlers/guild.py`: exists=True, hits=True
- Основні call sites:
  - `data/drop_tables.py:19` — `CENTRAL_DROP_MIGRATED_RULES = ("rune", "refine_stone", "equipment", "trophy", "potion")`
  - `data/drop_tables.py:265` — `"rule_id": "potion",`
  - `data/drop_tables.py:267` — `"group": "potion",`
  - `data/drop_tables.py:469` — `# ROM 11.6.0 CENTRAL POTION DROP`
  - `data/drop_tables.py:561` — `"potion",`
  - `data/runes.py:53` — `"sell_price": 0.0,`
  - `data/runes.py:66` — `"sell_price": 0.0,`
  - `data/runes.py:75` — `"sell_price": 0.0,`
  - `data/runes.py:84` — `"sell_price": 0.0,`
  - `db_modules/__init__.py:330` — `'create_guild', 'get_guild_creation_terms', 'get_user_guild', 'get_user_guild_member',`
  - `db_modules/connection.py:1` — `# ROM 17.19.1 MANA POTION PRICE BALANCE`
  - `db_modules/connection.py:90` — `sell_price REAL,`
  - `db_modules/connection.py:143` — `("items", "sell_price", "REAL DEFAULT 0"),`
  - `db_modules/connection.py:208` — `(401, "🔴 Мале зілля здоров'я", "potion_hp", "common", "potion", None, 1, 10, 1.00, 0, 0, 0, 0, 0, 0, 0),`
  - `db_modules/connection.py:209` — `(402, "🔵 Мале зілля мани", "potion_mp", "common", "potion", None, 1, 10, 0.80, 0, 0, 0, 0, 0, 0, 0),`
  - `db_modules/connection.py:210` — `(403, "🔴 Середнє зілля здоров'я", "potion_hp_medium", "common", "potion", None, 1, 10, 3.00, 0, 0, 0, 0, 0, 0, 0),`
  - `db_modules/connection.py:211` — `(404, "🔵 Середнє зілля мани", "potion_mp_medium", "common", "potion", None, 1, 10, 2.50, 0, 0, 0, 0, 0, 0, 0),`
  - `db_modules/connection.py:219` — `max_stack, sell_price,`
  - `db_modules/connection.py:232` — `sell_price=excluded.sell_price,`
  - `db_modules/dev_compat.py:109` — `def get_dynamic_sell_price(item_level, rarity):`

### Premium EXP і combat gold
- Статус: **PASS**
- Зафіксоване рішення: Premium gold bonus дозволений тільки для combat gold.
- Файлів із збігами: 23
- Очікувані owners:
  - `systems/premium_item_policy_system.py`: exists=True, hits=True
  - `systems/reward_system.py`: exists=True, hits=True
  - `handlers/timed_exp_bonus.py`: exists=True, hits=True
- Основні call sites:
  - `data/drop_tables.py:373` — `"group": "premium_material",`
  - `data/drop_tables.py:413` — `"group": "premium_material",`
  - `data/drop_tables.py:533` — `"bound_policy": "future_premium_bound_candidate",`
  - `data/rebirth_sphere_policy.py:9` — `"premium_bound": True,`
  - `data/rebirth_sphere_policy.py:17` — `"premium_bound": False,`
  - `db_modules/__init__.py:10` — `from systems.premium_item_policy_system import (`
  - `db_modules/__init__.py:11` — `init_premium_item_policy,`
  - `db_modules/__init__.py:12` — `get_premium_item_policy,`
  - `db_modules/__init__.py:15` — `get_premium_item_grants,`
  - `db_modules/__init__.py:503` — `__all__.extend(['init_premium_item_policy','get_premium_item_policy','can_grant_item_from_source','grant_item_from_source','get_premium_item_grants'])`
  - `handlers/auction_house.py:5136` — `"Досконалий Екстрактор, екіпіровані, зламані, bound/quest/DEV/premium та "`
  - `handlers/city.py:1203` — `_BUILD_MAIN_MENU_TEXT_BEFORE_EXP_BONUS_STATUS_17_30_1_1 = build_main_menu_text`
  - `handlers/city.py:1218` — `text = _BUILD_MAIN_MENU_TEXT_BEFORE_EXP_BONUS_STATUS_17_30_1_1(user_id, show_location_description=show_location_description)`
  - `handlers/city.py:1219` — `from systems.timed_exp_bonus_system import get_exp_bonus_account_summary`
  - `handlers/city.py:1220` — `summary = get_exp_bonus_account_summary(user_id)`
  - `handlers/city.py:1223` — `lines.extend(['💎 Premium: активний', '📈 Бонус за вбивство мобів: +25% EXP', f"⏳ Діє до: {_format_account_utc_17_30_1_1(summary.get('expires_at'))}"])`
  - `handlers/city.py:1225` — `lines.append('💎 Premium: неактивний')`
  - `handlers/city.py:1353` — `from systems.timed_exp_bonus_system import get_exp_bonus_account_summary`
  - `handlers/city.py:1354` — `summary = get_exp_bonus_account_summary(user_id)`
  - `handlers/city.py:1357` — `lines.extend(['💎 Premium: активний', '📈 Бонус за вбивство мобів: +25% EXP', f"⏳ Діє до: {_format_account_utc_17_30_1_1(summary.get('expires_at'))}"])`

### Адміністративні кристали
- Статус: **PASS**
- Зафіксоване рішення: Спочатку root-cause diagnosis; wallet/ledger policy не змінювати.
- Файлів із збігами: 13
- Очікувані owners:
  - `handlers/admin_crystal_credit.py`: exists=True, hits=True
  - `systems/admin_crystal_credit_system.py`: exists=True, hits=True
  - `systems/crystal_wallet_system.py`: exists=True, hits=True
- Основні call sites:
  - `config.py:20` — `ROM_ADMIN_CRYSTAL_CREDIT_MAX = _positive_int_env("ROM_ADMIN_CRYSTAL_CREDIT_MAX", "10000")`
  - `config.py:21` — `ROM_ADMIN_CRYSTAL_DEBIT_MAX = _positive_int_env("ROM_ADMIN_CRYSTAL_DEBIT_MAX", "10000")`
  - `db_modules/__init__.py:18` — `from systems.crystal_wallet_system import (`
  - `db_modules/__init__.py:19` — `init_crystal_wallet_system,`
  - `db_modules/__init__.py:20` — `get_crystal_wallet,`
  - `db_modules/__init__.py:22` — `credit_crystals,`
  - `db_modules/__init__.py:23` — `debit_crystals,`
  - `db_modules/__init__.py:501` — `__all__.extend(['init_crystal_wallet_system','get_crystal_wallet','get_crystal_balance','credit_crystals','debit_crystals','get_crystal_transactions','compensate_crystal_transaction'])`
  - `db_modules/dev_compat.py:378` — `protected_tables = {"users", "items", "inventory", "equipment_slots", "inventory_runes", "crystal_wallets", "crystal_transactions"}`
  - `handlers/admin_crystal_credit.py:9` — `from systems.admin_crystal_credit_system import is_admin,preview_admin_adjustment,execute_admin_adjustment,get_admin_adjustment_history,get_admin_adjustment_detail`
  - `handlers/admin_crystal_credit.py:10` — `states={};COMMAND='/admin_crystals'`
  - `handlers/admin_crystal_credit.py:56` — `def register_admin_crystal_credit_handlers(bot):`
  - `handlers/admin_crystal_credit.py:57` — `@bot.message_handler(commands=['admin_crystals'])`
  - `handlers/admin_crystal_credit.py:89` — `key=f"telegram:admin_crystal:{uid}:{call.message.chat.id}:{call.message.message_id}:{nonce}";result=execute_admin_adjustment(uid,state['target'],state['operation'],state['amount'],state['reason'],key)`
  - `handlers/crystal_shop.py:5` — `from systems.crystal_wallet_system import get_crystal_balance`
  - `handlers/dev.py:1084` — `from systems.crystal_wallet_system import get_crystal_balance`
  - `handlers/dev.py:1091` — `from systems.crystal_wallet_system import credit_crystals`
  - `handlers/dev.py:1096` — `result=credit_crystals(message.from_user.id,amount,"dev_credit",f"dev:credit:{message.from_user.id}:{message.message_id}",metadata={"telegram_message_id":message.message_id})`
  - `handlers/dev.py:1103` — `from systems.crystal_wallet_system import debit_crystals`
  - `handlers/dev.py:1108` — `result=debit_crystals(message.from_user.id,amount,"dev_debit",f"dev:debit:{message.from_user.id}:{message.message_id}",metadata={"telegram_message_id":message.message_id})`

### Тексти подорожі та прибуття
- Статус: **PASS**
- Зафіксоване рішення: Preview, route flavor і arrival text мають належати canonical metadata/resolver.
- Файлів із збігами: 40
- Очікувані owners:
  - `handlers/map.py`: exists=True, hits=True
  - `systems/travel_system.py`: exists=True, hits=True
  - `data/location_graph.py`: exists=True, hits=True
  - `data/locations.py`: exists=True, hits=True
- Основні call sites:
  - `data/classes.py:13` — `"description": (`
  - `data/classes.py:22` — `"description": (`
  - `data/classes.py:31` — `"description": (`
  - `data/classes.py:40` — `"description": (`
  - `data/classes.py:49` — `"description": (`
  - `data/classes.py:58` — `"description": (`
  - `data/location_graph.py:1` — `"""Canonical world-node graph for travel between locations."""`
  - `data/location_graph.py:3` — `TRAVEL_SECONDS = 20`
  - `data/location_graph.py:11` — `LOCATION_GRAPH = {`
  - `data/location_graph.py:21` — `return tuple(LOCATION_GRAPH.get(str(node_id), ()))`
  - `data/location_graph.py:26` — `def validate_location_graph():`
  - `data/location_graph.py:28` — `for node, neighbors in LOCATION_GRAPH.items():`
  - `data/location_graph.py:33` — `elif node not in LOCATION_GRAPH.get(neighbor, ()): errors.append(f"asymmetric edge: {node}->{neighbor}")`
  - `data/location_graph.py:34` — `if set(WORLD_NODES) != set(LOCATION_GRAPH): errors.append("WORLD_NODES and LOCATION_GRAPH keys differ")`
  - `data/location_graph.py:38` — `validate_location_graph()`
  - `data/locations.py:5` — `"description": (`
  - `data/locations.py:34` — `"description": (`
  - `data/story_quest_content.py:18` — `return StoryQuestDefinition(quest_id=d["quest_id"],number=d["number"],title=d["title"],quest_type=QuestType(d["quest_type"]),location_id=d["location_id"],unlock_level=d["unlock_level"],previous_quest_id=d.get("previous_quest_id"),giver_npc_id=d["giver_npc_id"],turn_in_npc_id=d.get("turn_in_npc_id"),`
  - `data/story_quest_definitions.py:73` — `description: str`
  - `data/story_quest_definitions.py:98` — `_require(_text(quest.description),f'{quest.quest_id}: description is required')`

### Class-aware спорядження з мобів
- Статус: **PASS**
- Зафіксоване рішення: Strict/weighted policy затверджується після окремого аудиту 20.6.3.
- Файлів із збігами: 14
- Очікувані owners:
  - `data/drop_tables.py`: exists=True, hits=True
  - `data/equipment_stat_policy.py`: exists=True, hits=True
  - `systems/drop_system.py`: exists=True, hits=True
  - `systems/dynamic_equipment_system.py`: exists=True, hits=True
  - `db_modules/generated_equipment.py`: exists=True, hits=True
- Основні call sites:
  - `data/drop_tables.py:111` — `"class_aware_chance": {`
  - `data/equipment_stat_policy.py:3` — `"""Canonical pure policy for class-aware generated equipment primary stats.`
  - `data/equipment_stat_policy.py:52` — `JEWELRY_STAT_WEIGHTS = MappingProxyType({`
  - `data/equipment_stat_policy.py:141` — `profile = JEWELRY_STAT_WEIGHTS[cls]`
  - `data/equipment_stat_policy.py:153` — `def validate_equipment_stat_policy() -> tuple[str, ...]:`
  - `data/equipment_stat_policy.py:159` — `("JEWELRY_STAT_WEIGHTS", JEWELRY_STAT_WEIGHTS),`
  - `data/equipment_stat_policy.py:183` — `def redistribute_primary_stat_budget(stats, class_key, equipment_kind, *, item_subtype="", chooser):`
  - `data/equipment_stat_policy.py:214` — `_POLICY_PROBLEMS = validate_equipment_stat_policy()`
  - `data/equipment_stat_policy.py:222` — `"JEWELRY_STAT_WEIGHTS", "ARMOR_STAT_WEIGHTS", "CLASS_ARMOR_TYPES",`
  - `data/equipment_stat_policy.py:225` — `"get_allowed_equipment_stats", "redistribute_primary_stat_budget",`
  - `data/equipment_stat_policy.py:226` — `"validate_equipment_stat_policy",`
  - `db_modules/__init__.py:142` — `from .generated_equipment import create_generated_equipment_item, create_generated_equipment_item_for_slot`
  - `db_modules/__init__.py:205` — `generate_class_shop_equipment, populate_class_shop_for_user`
  - `db_modules/__init__.py:314` — `'generate_class_shop_equipment', 'populate_class_shop_for_user',`
  - `db_modules/__init__.py:466` — `'create_generated_equipment_item',`
  - `db_modules/__init__.py:467` — `'create_generated_equipment_item_for_slot',`
  - `db_modules/dev_compat.py:13` — `from .generated_equipment import create_generated_equipment_item, create_generated_equipment_item_for_slot`
  - `db_modules/dev_compat.py:583` — `def generate_dynamic_equipment_stats(slot_key, item_level, rarity, weapon_hands=1, item_profile=None):`
  - `db_modules/dev_compat.py:1257` — `stats = generate_dynamic_equipment_stats(`
  - `db_modules/dev_compat.py:1438` — `stats = generate_dynamic_equipment_stats(`

## Наступний порядок

1. Stage 20.1.2 — економіка золота 1–10.
2. Stage 20.2.1 — аудит basic attack.
3. Stage 20.2.4 — lifecycle лікування Жреця.
4. Stage 20.3.1 — повний mana pipeline.
5. Незалежні read-only аудити admin crystals, travel і equipment generation можуть готуватися паралельно.

## Ручна перевірка

**Не потрібна.** Це read-only audit patch.

