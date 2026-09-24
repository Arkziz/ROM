# Stage 19.23: dependency-aware production import plan

## Рішення

**PASS_READY_FOR_AUTHORITATIVE_IMPORTER**

- HEAD before: `a3d7921f61aea41461d0ec257e18ba0cfb56d64b`
- Candidate SHA-256: `95b6ba349846821636d3e9024116cb71acd6b4d88ea0839170daaa78db9be260`
- Candidate quests: **50**
- Production source mutation: **ні**
- Production DB mutation: **ні**
- Candidate mutation: **ні**
- Ручна перевірка у грі: **не потрібна для цього plan-only підетапу**

## Authoritative policy

Candidate JSON залишається погодженим джерелом імпорту, але не runtime-authority. Production має отримати один authoritative definition/content path, без duplicate runtime registries.

## Field mapping

### definition_registry

- Candidate fields: `quest_id, number, title, quest_type, location_id, unlock_level, previous_quest_id, target_quantity`
- Owner candidates: `data/story_quest_definitions.py`
- Action: map into authoritative quest definitions; do not create a parallel runtime registry
- Dependency: existing definition schema and lifecycle engine
### content_registry

- Candidate fields: `description, objective_text, acceptance_text, completion_text, progress_text`
- Owner candidates: `data/story_quest_content.py`
- Action: store display text in one authoritative content path; normalize missing optional QUEST_ITEM text during import
- Dependency: NPC/profile renderers
### npc_registry

- Candidate fields: `giver_npc_id, turn_in_npc_id`
- Owner candidates: `data/story_quest_npcs.py, systems/story_quest_npc_acceptance_system.py`
- Action: bind only to canonical NPC IDs and existing story-capable routes
- Dependency: NPC registry and acceptance handlers
### reward

- Candidate fields: `reward`
- Owner candidates: `systems/story_quest_reward_system.py`
- Action: import fixed EXP/gold values, preserve fractional gold, keep quest 49 story reward separate from boss combat reward
- Dependency: exact-once reward adapter
### quest_item

- Candidate fields: `quest_item, required_quest_items, quest_item_consumption, retain_until_quest_id`
- Owner candidates: `systems/story_quest_item_drop_system.py`
- Action: map drop and consumption contracts; support non-consuming quest 24 and atomic three-item quest 30
- Dependency: dedicated quest item storage and completion transaction
### boss_completion

- Candidate fields: `boss_key, encounter_paths, guaranteed_call_after_success, retry_after_defeat_or_escape`
- Owner candidates: `systems/story_quest_boss_call_system.py, systems/story_quest_boss_completion_system.py`
- Action: map candidate policy to existing RNG and guaranteed-call systems without duplicating boss generation
- Dependency: boss registry, boss completion, guaranteed-call handler
### content_registry

- Candidate fields: `next_route, next_chapter, next_campaign_hint`
- Owner candidates: `data/story_quest_content.py`
- Action: treat as rendering or planning metadata; never use quest 50 to unlock dark_forest
- Dependency: canonical location unlock remains level 6


## Виявлена підготовча робота

- Runtime capability gaps для окремого cross-cutting підетапу: `multi_item_turn_in`.
- Owner-и, точний шлях яких потрібно підтвердити importer-патчем: `усі owner candidates знайдені`.

## Послідовність впровадження

- **19.23.1 · authoritative importer and schema adapters**: no quest activation; manual game check: ні; deliverables: candidate loader, field mapper, schema validator, import manifest verifier.
- **19.23.2 · cross-cutting runtime gaps**: only capabilities required by approved candidates; manual game check: так; deliverables: fractional gold verification, non-consuming TALK item prerequisite, atomic multi-item TURN_IN, optional narrative fallback.
- **19.23.3 · activate quests 1-10**: candidate batch 1-10 only; manual game check: так; deliverables: production definitions, content, NPC bindings, automated regression, rollback evidence.
- **19.23.4 · activate quests 11-20**: candidate batch 11-20 only; manual game check: так; deliverables: production definitions, content, NPC bindings, automated regression, rollback evidence.
- **19.23.5 · activate quests 21-30**: candidate batch 21-30 only; manual game check: так; deliverables: production definitions, content, NPC bindings, automated regression, rollback evidence.
- **19.23.6 · activate quests 31-40**: candidate batch 31-40 only; manual game check: так; deliverables: production definitions, content, NPC bindings, automated regression, rollback evidence.
- **19.23.7 · activate quests 41-50**: candidate batch 41-50 only; manual game check: так; deliverables: production definitions, content, NPC bindings, automated regression, rollback evidence.
- **19.23.8 · full campaign regression and documentation**: quests 1-50; manual game check: так; deliverables: fresh-character simulation, restart persistence, overlevel policy, boss retry/success, complete Stage 19 documentation.

## Обов’язкові правила mutation patch-ів

- backup до першої mutation;
- автоматичний rollback усіх змінених production-файлів на будь-який FAIL;
- не видаляти й не маніпулювати `game.db-wal` або `game.db-shm`;
- activation лише пакетами по 10;
- після кожного пакета надати конкретний manual game checklist;
- квест 49 зберігає окремі boss combat rewards і story reward ×5;
- квест 50 не обходить canonical unlock Темного Бору 6 рівня.

## Наступний patch

`patch_19_23_1_prepare_story_quest_authoritative_importer.py`
