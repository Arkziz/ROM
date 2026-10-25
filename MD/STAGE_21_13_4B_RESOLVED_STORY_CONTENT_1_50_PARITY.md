# Stage 21.13.4b - Resolved Story content 1-50 parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Contract matrix: **11/11 RESOLVED**
- Canonical records: **50/50**
- False duplicate quest 49: **RESOLVED**
- Authorized package: **1-10**
- Packages 11-50: **NOT_AUTHORIZED YET**
- Runtime integration: **NOT_AUTHORIZED**
- Production persistence: **NOT_AUTHORIZED**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

### EXACT_QUEST_RECORDS_1_TO_50

The only canonical record set for migration planning is the 50 ordered objects in $.quests of Квести/ROM_квести_Початок_Шляху_candidate.json. Quest identity is the explicit numeric quest number plus the stable content ID carried by that record. Nested policy objects are references, not quest records. Therefore the apparent duplicate 49 is false and the authoritative matrix contains exactly one record for every number 1-50.

Typed reasons: missing_quest_record, duplicate_quest_number, out_of_order_chain, invalid_stable_id

### LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES

Required levels are fixed by package: 1-10 level 1, 11-20 level 2, 21-30 level 3, 31-40 level 4, 41-50 level 5. Quest 1 has no predecessor. Every quest N from 2 through 50 requires quest N-1 completed or skipped under the existing overlevel/SKIP policy. Both level and predecessor must pass before availability.

Typed reasons: level_too_low, predecessor_not_satisfied, chain_gap

### OBJECTIVES_TARGETS_AND_QUEST_ITEMS

Each quest uses only its candidate-declared canonical objective, target, region/mob/NPC identity and quest-item metadata. No default objectives or targets are inferred. Quest items remain in the isolated store, declared 15% drop chances stay quest-specific, accumulated items are consumed only by the declared exact-once turn-in, and duplicate combat/drop events cannot advance progress twice.

Typed reasons: unsupported_objective, invalid_target, quest_item_mismatch, duplicate_event

### REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY

Rewards are resolved as content references through the canonical reward pipeline, not embedded formulas. Quests 1-10 use full triple canonical normal-mob level-1 rewards; 11-20 use level-2; 21-30 use level-3, including TALK, QUEST_ITEM and TURN_IN. Quests 31-50 must use only reward policy explicitly present in candidate/V1 evidence; no extrapolation from 1-30 is authorized.

Typed reasons: reward_policy_missing, reward_reference_invalid, reward_formula_in_content

### NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES

Every record must use stable canonical NPC and location IDs validated against the NPC/location registries. User-visible location text is resolved as Початок Шляху. Raw start_path, raw NPC IDs, automatic title-casing and the term глава are forbidden in presentation metadata. Handlers consume typed content and do not own quest-specific conditions.

Typed reasons: unknown_npc_reference, unknown_location_reference, technical_id_disclosure, forbidden_term

### BOSS_AND_FORCED_ENCOUNTER_CONTRACT

Ordinary location bosses continue to appear through Hunting. Quest 49 additionally authorizes the candidate-declared guaranteed story call for the Pack Leader, using shared boss/combat formulas and the player-level boss rule. Defeat or escape permits retry; victory records exact-once progress and blocks another guaranteed call. Boss combat reward remains separate from story turn-in reward.

Typed reasons: wrong_boss_key, wrong_location, forced_call_already_won, stale_boss_event

### PACKAGE_BY_TEN_AND_CONTENT_VALIDATION

Implementation is split into five mutation packages under canonical Stage 21.13.4: 1-10, 11-20, 21-30, 31-40 and 41-50. Each package requires an executable manifest check for record count, ordered IDs, stable IDs, predecessor links, level gate, objective schema, NPC/location references, quest items, rewards, localization and duplicates before the next package is authorized.

Typed reasons: package_manifest_invalid, cross_package_gap, content_validation_failed

### QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE

Quest 49 completes its BOSS objective only on exact Pack Leader victory in the correct location, then remains pending until turn-in to the Mercenary Guild Leader. Quest 50 is the itemless final turn-in/talk with the Elder and marks the Початок Шляху story complete; dark_forest remains a hint, not automatic unlock. V2 must display persisted 1/1 progress after quest-49 victory, correcting the known V1 presentation defect without changing combat, reward or completion semantics.

Typed reasons: boss_not_defeated, turn_in_npc_mismatch, terminal_state_invalid, progress_presentation_mismatch

## Next patch

`patch_21_13_4c_implement_story_content_1_10.py`
