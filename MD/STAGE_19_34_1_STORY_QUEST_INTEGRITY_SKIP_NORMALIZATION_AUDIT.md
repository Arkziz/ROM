# Stage 19.34.1: аудит цілісності, SKIP і нормалізації сюжетних квестів

- Audit decision: **NO_GO**
- Production mutation: **NO**
- Production coverage: **1–100**

## A. Quest-item identity

- Verdict: **ISOLATED_ITEM_KEY_NAMESPACE**
- Canonical identity: `quest_id + item_key` in `user_story_quest_items`.
- Numeric `id` is a local row identifier, not an `items.id` type namespace.
- `inventory_id` and `item_id` are absent from the isolated quest-item schema.

## B. Overlevel SKIP

- Verdict: **NO_GO_MUTATION_REQUIRED**
- **ACTIVE_ONLY_SKIP**: Current policy skips at most one persisted ACTIVE quest; derived AVAILABLE/LOCKED quests are not materialized as SKIPPED.
- **NO_CAMPAIGN_RECONCILIATION**: No atomic location-wide reconciliation exists for all unfinished quests after crossing a location level ceiling.

Recommended policy: atomically materialize every unfinished quest of an exceeded location as `SKIPPED`, preserve `COMPLETED`, claim no rewards, remove isolated quest items, and emit one summary message.

## C. Technical and balance normalization

- Verdict: **NO_GO_NORMALIZATION_REQUIRED**
- KILL_REGION target distribution: `{3: 1, 5: 1, 6: 2, 8: 7, 10: 10, 12: 2, 15: 2}`.
- Packages outside recommended 8/10 policy: **6**.
- Navigation findings: **23**.
- Duplicate quest item keys: **0**.

## D. Candidate synchronization

- Verdict: **PASS**.
- Differences: **0**.

## Proposed mutation order

1. `Stage 19.34.2`: atomic location-wide overlevel SKIP.
2. `Stage 19.34.3`: quest-item identity hardening and namespace documentation.
3. `Stage 19.34.4`: technical/UI/navigation normalization.
4. `Stage 19.34.5`: KILL_REGION 8/10 balance normalization and active-progress reconciliation.
5. `Stage 19.34.6`: production/candidate/documentation synchronization.
6. `Stage 19.34.7`: acceptance.
