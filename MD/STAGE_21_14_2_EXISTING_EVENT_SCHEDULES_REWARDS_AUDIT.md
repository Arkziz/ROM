# Stage 21.14.2: Existing Event Schedules and Rewards Audit

## Result
- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- Branch: `rewrite/rom-v2`
- Starting HEAD: `1f1ed0db9ea0cabd608508b99ee54823984a5731`
- V1 Python files scanned: **1087**
- Evidence rows: **3008**
- Source files: **409**
- Schedule source files: **110**
- Reward source files: **296**

## Safety and scope
This is a static read-only V1 audit. It does not import V1 runtime modules, start the game,
open SQLite, connect Telegram/runtime, or modify production source. `game.db-wal` and
`game.db-shm` were not read, deleted, cleared, copied, restored, or otherwise manipulated.

## Contract boundaries
- Static matches are evidence, not automatic V2 rules.
- Timezone, inclusivity, recurrence, eligibility and restart behavior require owner evidence.
- Reward IDs, quantities, currencies, operation keys and exact-once behavior require owner evidence.
- Historical and duplicate definitions cannot be selected mechanically.
- Implementation remains unauthorized until refinement and parity resolution complete.

## Roadmap evidence
```json
[]
```

## Evidence preview
- `config.py:6` | **REWARD** | `<module>` |  | TOKEN = os.getenv("BOT_TOKEN") | 
- `config.py:23` | **REWARD** | `<module>` |  | if not TOKEN: | raise RuntimeError("BOT_TOKEN не знайдено у .env")
- `config.py:24` | **REWARD** | `<module>` | if not TOKEN: | raise RuntimeError("BOT_TOKEN не знайдено у .env") | 
- `data/about_game.py:68` | **REWARD** | `<module>` |  | Руни, жетони та спеціальні матеріали мають окремі джерела отримання. Не всі з них можуть випадати зі звичайних ворогів, продаватися або передаватися іншим гравцям.'''}, | "guilds":{"button":"🏰 Гільдії","title":"🏰 Гільдії","text":'''Гільдії об’єднують гравців для спільного розвитку. Учасники можуть виконувати активності, розвивати гільдію, переглядати журнал подій і змагатися в рейтингах.
- `data/about_game.py:89` | **REWARD** | `<module>` |  | • Виконуйте щоденні завдання та контракти, щоб отримувати додаткові нагороди. | 
- `data/about_game.py:97` | **REWARD** | `<module>` |  | • Небезпечніші вороги можуть принести кращу нагороду, але потребують кращої підготовки.'''} } | def get_about_game_section(key): return ABOUT_GAME_SECTIONS.get(str(key or ""))
- `data/balance.py:19` | **SCHEDULE** | `<module>` | CONTRACT_TARGET_KILLS = 5 | DAILY_CONTRACT_LIMIT = 5 | DAILY_QUEST_ID_KILL_MONSTERS = 'kill_25_monsters'
- `data/balance.py:20` | **SCHEDULE_AND_REWARD** | `<module>` | DAILY_CONTRACT_LIMIT = 5 | DAILY_QUEST_ID_KILL_MONSTERS = 'kill_25_monsters' | DAILY_QUEST_REWARD_ITEM_ID = 401
- `data/balance.py:21` | **SCHEDULE_AND_REWARD** | `<module>` | DAILY_QUEST_ID_KILL_MONSTERS = 'kill_25_monsters' | DAILY_QUEST_REWARD_ITEM_ID = 401 | DAILY_QUEST_REWARD_QUANTITY = 3
- `data/balance.py:22` | **SCHEDULE_AND_REWARD** | `<module>` | DAILY_QUEST_REWARD_ITEM_ID = 401 | DAILY_QUEST_REWARD_QUANTITY = 3 | DAILY_QUEST_TARGET_KILLS = 25
- `data/balance.py:23` | **SCHEDULE_AND_REWARD** | `<module>` | DAILY_QUEST_REWARD_QUANTITY = 3 | DAILY_QUEST_TARGET_KILLS = 25 | ENERGY_MAX = 40
- `data/balance.py:41` | **SCHEDULE** | `<module>` | 'CONTRACT_TARGET_KILLS', | 'DAILY_CONTRACT_LIMIT', | 'DAILY_QUEST_ID_KILL_MONSTERS',
- `data/balance.py:42` | **SCHEDULE_AND_REWARD** | `<module>` | 'DAILY_CONTRACT_LIMIT', | 'DAILY_QUEST_ID_KILL_MONSTERS', | 'DAILY_QUEST_REWARD_ITEM_ID',
- `data/balance.py:43` | **SCHEDULE_AND_REWARD** | `<module>` | 'DAILY_QUEST_ID_KILL_MONSTERS', | 'DAILY_QUEST_REWARD_ITEM_ID', | 'DAILY_QUEST_REWARD_QUANTITY',
- `data/balance.py:44` | **SCHEDULE_AND_REWARD** | `<module>` | 'DAILY_QUEST_REWARD_ITEM_ID', | 'DAILY_QUEST_REWARD_QUANTITY', | 'DAILY_QUEST_TARGET_KILLS',
- `data/balance.py:45` | **SCHEDULE_AND_REWARD** | `<module>` | 'DAILY_QUEST_REWARD_QUANTITY', | 'DAILY_QUEST_TARGET_KILLS', | 'ENERGY_MAX',
- `data/bosses.py:4` | **REWARD** | `<module>` | This module contains data only. It does not select encounters, mutate combat, | write to SQLite, award rewards, or call Telegram APIs. | """
- `data/drop_tables.py:7` | **REWARD** | `<module>` |  | Existing reward_system and rune_system behavior remains authoritative until the | 
- `data/drop_tables.py:35` | **REWARD** | `<module>` |  | "currency_direct", | 
- `data/runes.py:28` | **REWARD** | `<module>` | RUNE_ITEM_ID_END = 725 | FIRIUS_TOKEN_ITEM_ID = 726 | RUNE_EXTRACTOR_ITEM_ID = 727
- `data/runes.py:31` | **SCHEDULE_AND_REWARD** | `<module>` | PERFECT_RUNE_EXTRACTOR_ITEM_ID = 728 | FIRIUS_TOKENS_PER_DAILY_REWARD = 3 | RUNE_FUSION_SOURCE_QUANTITY = 3
- `data/runes.py:33` | **REWARD** | `<module>` | RUNE_FUSION_SOURCE_QUANTITY = 3 | RUNE_FUSION_TOKEN_QUANTITY = 1 | RUNE_MAX_STACK = 50
- `data/runes.py:35` | **REWARD** | `<module>` | RUNE_MAX_STACK = 50 | FIRIUS_TOKEN_MAX_STACK = 999 | EXTRACTOR_MAX_STACK = 50
- `data/runes.py:59` | **REWARD** | `<module>` | RUNE_UTILITY_ITEM_DEFINITIONS = { | FIRIUS_TOKEN_ITEM_ID: { | "id": FIRIUS_TOKEN_ITEM_ID,
- `data/runes.py:60` | **REWARD** | `<module>` | FIRIUS_TOKEN_ITEM_ID: { | "id": FIRIUS_TOKEN_ITEM_ID, | "name": "🪙 Жетон Фіріуса",
- `data/runes.py:61` | **REWARD** | `<module>` | "id": FIRIUS_TOKEN_ITEM_ID, | "name": "🪙 Жетон Фіріуса", | "type": "firius_token",
- `data/runes.py:62` | **REWARD** | `<module>` | "name": "🪙 Жетон Фіріуса", | "type": "firius_token", | "rarity": "common",
- `data/runes.py:65` | **REWARD** | `<module>` | "category": "material", | "max_stack": FIRIUS_TOKEN_MAX_STACK, | "sell_price": 0.0,
- `data/story_quest_content.py:14` | **REWARD** | `<module>` | from types import MappingProxyType | from data.story_quest_definitions import NavigationDefinition,QuestItemDefinition,RequiredQuestItemDefinition,RewardDefinition,StoryQuestDefinition,QuestType,validate_story_quest_pack | _DATA = list((*START_PATH_01_10, *START_PATH_11_20, *START_PATH_21_30, *START_PATH_31_40, *START_PATH_41_50, *DARK_FOREST_51_60, *DARK_FOREST_61_70, *DARK_FOREST_71_80, *DARK_FOREST_81_90, *DARK_FOREST_91_100))
- `data/story_quest_content.py:18` | **REWARD** | `_definition` | d=row["definition"]; item=d.get("quest_item"); nav=d["navigation"] | return StoryQuestDefinition(quest_id=d["quest_id"],number=d["number"],title=d["title"],quest_type=QuestType(d["quest_type"]),location_id=d["location_id"],unlock_level=d["unlock_level"],previous_quest_id=d.get("previous_quest_id"),giver_npc_id=d["giver_npc_id"],turn_in_npc_id=d.get("turn_in_npc_id"),description=d["description"],objective_text=d["objective_text"],target_quantity=d["target_quantity"],boss_key=d.get("boss_key"),quest_item=QuestItemDefinition(**item) if item else None,required_quest_items=tuple(RequiredQuestItemDefinition(**x) for x in d.get("required_quest_items",[])),quest_item_consumption=d.get("quest_item_co
- `data/story_quest_definitions.py:26` | **REWARD** | `RewardDefinition` | @dataclass(frozen=True) | class RewardDefinition: | """Candidate reward payload. Final values remain balance-controlled content."""
- `data/story_quest_definitions.py:27` | **REWARD** | `RewardDefinition` | class RewardDefinition: | """Candidate reward payload. Final values remain balance-controlled content.""" | exp: int=0
- `data/story_quest_definitions.py:80` | **REWARD** | `StoryQuestDefinition` | quest_item_consumption: str = "default" | reward: RewardDefinition=field(default_factory=RewardDefinition) | navigation: Optional[NavigationDefinition]=None
- `data/story_quest_definitions.py:101` | **REWARD** | `validate_story_quest_definition` | _require(quest.target_quantity>0,f'{quest.quest_id}: target_quantity must be positive') | _require(quest.reward.exp>=0 and quest.reward.gold>=0,f'{quest.quest_id}: rewards cannot be negative') | if quest.quest_type is QuestType.QUEST_ITEM:
- `data/story_quests/dark_forest_51_60.py:34` | **REWARD** | `<module>` | 'дозори та рунічний слід, що веде до Темного Бору.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:87` | **REWARD** | `<module>` | 'помітили, що гобліни діють організовано.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:138` | **REWARD** | `<module>` | 'та контролюють прикордонний шлях.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:186` | **REWARD** | `<module>` | 'потрібно передати Старості.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:237` | **REWARD** | `<module>` | 'шляху.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [{'item_key': 'dark_forest_goblin_patrol_border_sign',
- `data/story_quests/dark_forest_51_60.py:287` | **REWARD** | `<module>` | 'розвідки.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:336` | **REWARD** | `<module>` | 'передати Рунному Майстру.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:390` | **EVENT_CONTEXT** | `<module>` | 'Я залишу уламок для подальшого дослідження. Його руна ' | 'підтверджує зв’язок між подіями на Початку Шляху та загрозою ' | 'у Темному Борі.',
- `data/story_quests/dark_forest_51_60.py:395` | **REWARD** | `<module>` | 'дозори пов’язані з джерелом корупції в глибині Темного Бору.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [{'item_key': 'dark_forest_runic_amulet_fragment',
- `data/story_quests/dark_forest_51_60.py:416` | **EVENT_CONTEXT** | `<module>` | 'Я залишу уламок для подальшого дослідження. Його руна підтверджує зв’язок ' | 'між подіями на Початку Шляху та загрозою у Темному Борі.', | 'completion_text': 'Рунний Майстер підтверджує: символ на амулеті належить до тієї самої системи '
- `data/story_quests/dark_forest_51_60.py:453` | **REWARD** | `<module>` | 'впорядкована мережа таборів.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:500` | **EVENT_CONTEXT** | `<module>` | 'Твоєї доповіді достатньо, щоб підтвердити: загроза Темного ' | 'Бору організована й пов’язана з подіями на Початку Шляху. ' | 'Перша розвідка завершена.',
- `data/story_quests/dark_forest_51_60.py:503` | **EVENT_CONTEXT** | `<module>` | 'completion_text': 'Староста приймає доповідь про гоблінські дозори та рунічний ' | 'амулет. Перша розвідка підтвердила: події на Початку Шляху й ' | 'загроза Темного Бору є частинами одного задуму.\n'
- `data/story_quests/dark_forest_51_60.py:510` | **REWARD** | `<module>` | '✅ Розділ «Тінь за Темним Бором» завершено.', | 'reward': {'exp': 66, 'gold': 1.84}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_51_60.py:527` | **EVENT_CONTEXT** | `<module>` | 'Твоєї доповіді достатньо, щоб підтвердити: загроза Темного Бору організована ' | 'й пов’язана з подіями на Початку Шляху. Перша розвідка завершена.', | 'completion_text': 'Староста приймає доповідь про гоблінські дозори та рунічний амулет. Перша '
- `data/story_quests/dark_forest_51_60.py:529` | **EVENT_CONTEXT** | `<module>` | 'completion_text': 'Староста приймає доповідь про гоблінські дозори та рунічний амулет. Перша ' | 'розвідка підтвердила: події на Початку Шляху й загроза Темного Бору є ' | 'частинами одного задуму.\n'
- `data/story_quests/dark_forest_61_70.py:31` | **REWARD** | `<module>` | 'внутрішніх стоянок і узгоджений рух гоблінських патрулів.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:76` | **REWARD** | `<module>` | 'ділянкою біля поваленого дуба.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:122` | **REWARD** | `<module>` | 'обмінюються звуковими сигналами.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:168` | **REWARD** | `<module>` | 'металевому обручі.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:219` | **REWARD** | `<module>` | 'нанесено навмисно та розподілено на окремі групи.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [{'item_key': 'dark_forest_goblin_signal_horn',
- `data/story_quests/dark_forest_61_70.py:270` | **REWARD** | `<module>` | 'зниклим караваном.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:318` | **REWARD** | `<module>` | 'через цю ділянку зупинено.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:338` | **REWARD** | `<module>` | 'drop_message': ''}, | {'definition': {'quest_id': 'dark_forest_068_heavy_token', | 'number': 68,
- `data/story_quests/dark_forest_61_70.py:340` | **REWARD** | `<module>` | 'number': 68, | 'title': 'Важкий жетон', | 'quest_type': 'QUEST_ITEM',
- `data/story_quests/dark_forest_61_70.py:360` | **REWARD** | `<module>` | 'не показуй гоблінам, якщо вони помітять тебе раніше.', | 'completion_text': 'Знайдено важкий залізний жетон із символом трьох зубців і ' | 'сімома зарубками на звороті.',
- `data/story_quests/dark_forest_61_70.py:362` | **REWARD** | `<module>` | 'сімома зарубками на звороті.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [],
- `data/story_quests/dark_forest_61_70.py:364` | **REWARD** | `<module>` | 'required_quest_items': [], | 'quest_item': {'item_key': 'dark_forest_goblin_patrol_command_token', | 'display_name': 'Командний жетон гоблінського дозору',
- `data/story_quests/dark_forest_61_70.py:365` | **REWARD** | `<module>` | 'quest_item': {'item_key': 'dark_forest_goblin_patrol_command_token', | 'display_name': 'Командний жетон гоблінського дозору', | 'required_quantity': 1,
- `data/story_quests/dark_forest_61_70.py:383` | **REWARD** | `<module>` | 'гоблінам, якщо вони помітять тебе раніше.', | 'completion_text': 'Знайдено важкий залізний жетон із символом трьох зубців і сімома зарубками ' | 'на звороті.',
- `data/story_quests/dark_forest_61_70.py:386` | **REWARD** | `<module>` | 'progress_text': 'Пошук металевого предмета дозорного: {progress}/1', | 'drop_message': '🧩 Сюжетна знахідка: Командний жетон гоблінського дозору'}, | {'definition': {'quest_id': 'dark_forest_069_seven_notches',
- `data/story_quests/dark_forest_61_70.py:393` | **REWARD** | `<module>` | 'unlock_level': 7, | 'previous_quest_id': 'dark_forest_068_heavy_token', | 'giver_npc_id': 'trader',
- `data/story_quests/dark_forest_61_70.py:397` | **REWARD** | `<module>` | 'target_quantity': 1, | 'description': 'Показати Торговцю залізний жетон і з’ясувати можливе значення ' | 'семи зарубок.',
- `data/story_quests/dark_forest_61_70.py:399` | **REWARD** | `<module>` | 'семи зарубок.', | 'objective_text': 'Показати Торговцю командний жетон гоблінського дозору.', | 'acceptance_text': 'Символ на лицьовому боці такий самий, як на зниклих ящиках. '
- `data/story_quests/dark_forest_61_70.py:407` | **REWARD** | `<module>` | '\n' | 'Якщо гобліни перейняли цю систему, жетон пов’язаний із сьомим ' | 'внутрішнім маршрутом. Більше я за ним визначити не зможу.',
- `data/story_quests/dark_forest_61_70.py:409` | **REWARD** | `<module>` | 'внутрішнім маршрутом. Більше я за ним визначити не зможу.', | 'completion_text': 'Торговець оглядає жетон і підтверджує, що сім зарубок можуть ' | 'позначати окремий маршрут або кінцевий пункт доставки.',
- `data/story_quests/dark_forest_61_70.py:411` | **REWARD** | `<module>` | 'позначати окремий маршрут або кінцевий пункт доставки.', | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [{'item_key': 'dark_forest_goblin_patrol_command_token',
- `data/story_quests/dark_forest_61_70.py:412` | **REWARD** | `<module>` | 'reward': {'exp': 75, 'gold': 2.36}, | 'required_quest_items': [{'item_key': 'dark_forest_goblin_patrol_command_token', | 'quantity': 1,
- `data/story_quests/dark_forest_61_70.py:429` | **REWARD** | `<module>` | '\n' | 'Якщо гобліни перейняли цю систему, жетон пов’язаний із сьомим внутрішнім ' | 'маршрутом. Більше я за ним визначити не зможу.',
- `data/story_quests/dark_forest_61_70.py:431` | **REWARD** | `<module>` | 'маршрутом. Більше я за ним визначити не зможу.', | 'completion_text': 'Торговець оглядає жетон і підтверджує, що сім зарубок можуть позначати ' | 'окремий маршрут або кінцевий пункт доставки.',
- `data/story_quests/dark_forest_61_70.py:433` | **REWARD** | `<module>` | 'окремий маршрут або кінцевий пункт доставки.', | 'progress_text': 'Показати Торговцю командний жетон гоблінського дозору.', | 'drop_message': ''},
- `data/story_quests/dark_forest_61_70.py:435` | **REWARD** | `<module>` | 'drop_message': ''}, | {'definition': {'quest_id': 'dark_forest_070_seventh_camp', | 'number': 70,
- `data/story_quests/dark_forest_61_70.py:445` | **REWARD** | `<module>` | 'target_quantity': 1, | 'description': 'Передати Голові Найманців жетон із сімома зарубками для ' | 'зіставлення з картою гоблінських маршрутів.',
- `data/story_quests/dark_forest_61_70.py:447` | **REWARD** | `<module>` | 'зіставлення з картою гоблінських маршрутів.', | 'objective_text': 'Передати Голові Найманців командний жетон гоблінського дозору.', | 'acceptance_text': 'Сім зарубок пояснюють те, що досі не складалося в єдину '
- `data/story_quests/dark_forest_61_70.py:458` | **REWARD** | `<module>` | '\n' | 'Я залишу жетон для порівняння з маршрутами розвідників. Тепер ' | 'ми маємо доказ, що мережа гоблінських дозорів більша, ніж '
- `data/story_quests/dark_forest_61_70.py:461` | **REWARD** | `<module>` | 'здавалося.', | 'completion_text': 'Голова Найманців приймає жетон і підтверджує існування ' | 'сьомого внутрішнього маршруту.\n'

Full evidence with hashes: `reports/stage_21_14_2_existing_event_schedules_rewards_audit.json`.

## Next action
**GO_TO_SEMANTIC_REFINEMENT**. Manual in-game verification: **NOT REQUIRED**, audit-only stage.
