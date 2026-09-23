# Stage 19.14: аудит власників нагород сюжетних квестів

## Статус

- Тип: **read-only**
- HEAD: `c7d9cd1198d720b783c9da58635625cd2069780e`
- Production DB mutation: **ні**
- Висновок: **поточні public `add_exp` / `add_gold` не можна напряму викликати з reward adapter**

## Короткий висновок

Stage 19.8 правильно вимагає, щоб reward adapter використовував той самий SQLite connection і не виконував commit/rollback. Поточний canonical EXP owner має власний `BEGIN IMMEDIATE` і завершує транзакцію самостійно. Тому прямий виклик `db.add_exp()` з completion transaction порушив би атомарність `quest items → reward → COMPLETED`.

## Власники

### `systems.player_system.add_exp`

- Found: `True`
- Definitions: `1`
- Authoritative line: `1831`
- Parameters: `['user_id', 'amount']`
- BEGIN IMMEDIATE: `True`
- Commit: `True`
- Rollback: `True`
- Explicit connection parameter: `False`

### `systems.player_system.add_gold`

- Found: `True`
- Definitions: `2`
- Authoritative line: `1273`
- Parameters: `['user_id', 'amount']`
- BEGIN IMMEDIATE: `False`
- Commit: `True`
- Rollback: `False`
- Explicit connection parameter: `False`

### `db.add_exp`

- Found: `False`
- Definitions: `0`
- Authoritative line: `n/a`
- Parameters: `[]`
- BEGIN IMMEDIATE: `False`
- Commit: `False`
- Rollback: `False`
- Explicit connection parameter: `False`

### `db.add_gold`

- Found: `False`
- Definitions: `0`
- Authoritative line: `n/a`
- Parameters: `[]`
- BEGIN IMMEDIATE: `False`
- Commit: `False`
- Rollback: `False`
- Explicit connection parameter: `False`

### `systems.level_up_reward_system.apply_level_up_rewards_in_transaction`

- Found: `True`
- Definitions: `1`
- Authoritative line: `393`
- Parameters: `['db', 'user_id', 'old_level', 'new_level']`
- BEGIN IMMEDIATE: `False`
- Commit: `False`
- Rollback: `False`
- Explicit connection parameter: `True`

### `systems.story_quest_completion_system.complete_active_story_quest`

- Found: `True`
- Definitions: `1`
- Authoritative line: `52`
- Parameters: `['connection']`
- BEGIN IMMEDIATE: `False`
- Commit: `False`
- Rollback: `False`
- Explicit connection parameter: `True`

## Findings

### F1 · BLOCKER · Canonical add_exp owns an independent transaction

systems.player_system.add_exp uses the global DB owner, begins BEGIN IMMEDIATE, commits/rolls back internally, and does not accept the explicit connection owned by story completion. It cannot be called from the Stage 19.8 reward_adapter without breaking atomicity.

Confirmed: `True`

### F2 · HIGH · db.add_exp is only a compatibility wrapper

db.add_exp delegates to systems.player_system.add_exp and therefore does not provide a transaction-compatible alternative.

Confirmed: `False`

### F3 · HIGH · Gold owner requires explicit-connection parity

Canonical add_gold does not expose a same-connection API suitable for exact-once completion. Stage 19.15 must add a narrow in-transaction primitive or perform the canonical users.gold update through the supplied connection with maintained parity tests.

Confirmed: `True`

### F4 · HIGH · Level-up side effects are part of canonical EXP semantics

Quest EXP must preserve level thresholds, free attribute points, max HP recalculation, level-up reward ledger/items and the structured level-up result/message contract. A direct level/exp-only UPDATE is forbidden.

Confirmed: `True`

### F5 · MEDIUM · Overlevel SKIP must run after committed reward level-up

Stage 19.15 should return a production-shaped level result, while notification and location-range SKIP remain post-commit orchestration. Do not send Telegram messages inside the completion transaction.

Confirmed: `True`

## Рекомендований scope Stage 19.15

- Add explicit-connection EXP and gold mutation primitives under the canonical player/reward owner.
- Refactor existing add_exp to reuse the same core while preserving its public contract.
- Keep BEGIN/commit/rollback in the caller for the new in-transaction path.
- Preserve level thresholds, attribute points, max HP, level-up rewards and idempotency.
- Make the story reward adapter use the supplied completion connection only.
- Return exp, gold, old/new level, reached levels and level-up reward message data.
- Run overlevel SKIP and user notifications only after successful completion commit.

## Заборонені shortcuts

- Calling db.add_exp from inside complete_active_story_quest reward_adapter.
- Opening a second connection or committing inside the adapter.
- Updating only users.level/users.exp and bypassing level-up side effects.
- Sending Telegram messages before the transaction commits.
- Creating a second story-specific EXP curve or gold wallet.

## DB evidence

- quick_check: `ok`
- foreign_key_violations: `0`
- story tables: `['user_story_quest_items', 'user_story_quests']`

## Наступний patch

`patch_19_15_integrate_story_quest_reward_adapter.py`
