# Stage 21.13.4a - Refined Story content 1-50 contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Contract matrix: **3 confirmed / 8 review-required / 11 total**
- Candidate quest IDs discovered: **50**
- Missing candidate IDs: **[]**
- Duplicate candidate IDs: **{'49': 2}**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### EXACT_QUEST_RECORDS_1_TO_50

Confirmed:

- canonical candidate JSON is parsed structurally rather than searched only by literals
- quest-like dictionaries are indexed by stable numeric identity when present
- missing and duplicate candidate IDs are reported explicitly
- production definition builders, imports and call sites are inventoried

Remaining question: Resolve the exact authoritative record for every quest ID 1-50, including title, description, objective, target, NPC references, location, rewards and predecessor; reconcile candidate records against the actual production builder output without treating text or array position as identity.

### LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES

Confirmed:

- the canonical chain boundary is 1-50
- the approved package gates are 1-10 level 1, 11-20 level 2, 21-30 level 3, 31-40 level 4 and 41-50 level 5
- each package requires the corresponding level
- the chain requires completion or authorized SKIP of the previous quest

Remaining question: Extract the actual candidate and V1 fields that encode required level and predecessor, then produce a 50-row executable matrix proving exact package gates, quest 1 root semantics and quest N predecessor N-1 for N=2..50.

### OBJECTIVES_TARGETS_AND_QUEST_ITEMS

Confirmed:

- V1 supports TALK, KILL_REGION, QUEST_ITEM, TURN_IN and BOSS through the Quest Engine contract
- candidate records expose their available objective-shaped fields for exact reconciliation
- quest items must remain isolated from regular inventory
- known approved quest-item chances and special target rules must not be generalized beyond their quests

Remaining question: Resolve every quest objective type, target, region/mob identity, quest-item key, quantity, 15% drop chance where approved, accumulation/consumption boundary and exact-once event identity; flag every candidate/production mismatch rather than inventing defaults.

### REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY

Confirmed:

- rewards are content data consumed by the generic Quest Engine
- packages 1-10, 11-20 and 21-30 have approved full triple rewards based on canonical normal mobs of levels 1, 2 and 3 respectively
- TALK, QUEST_ITEM and TURN_IN receive the same package policy where approved
- reward formulas must not be copied into content definitions

Remaining question: Locate the canonical reward resolver inputs and determine exact reward references for quests 1-50; preserve approved package policies and identify unresolved policy for 31-50 from actual V1 evidence instead of extrapolating.

### NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES

Confirmed:

- stable NPC IDs and location assignment have API-ready owners
- the user-facing location name must be Початок Шляху
- technical start_path remains allowed only as identity
- handlers must not own quest-specific conditions

Remaining question: Resolve start/completion NPC IDs, canonical location IDs and localized presentation references for every quest; verify all referenced NPCs and routes exist and prohibit raw technical location/NPC IDs or the term глава in user-visible metadata.

### BOSS_AND_FORCED_ENCOUNTER_CONTRACT

Confirmed:

- boss objectives are owned by shared combat and Quest Engine boundaries
- the location boss normally appears through Hunting, not a separate boss button
- quest 49 has an accepted forced leader encounter and completion flow
- new boss formulas or encounter rules are not authorized

Remaining question: Locate the exact V1 forced-encounter evidence for quest 49, boss identity/level behavior, exact-once victory evidence and retry/restart semantics; distinguish ordinary random boss encounters from quest-forced encounter orchestration.

### PACKAGE_BY_TEN_AND_CONTENT_VALIDATION

Confirmed:

- roadmap requires migration in packages of ten
- candidate content covers the Початок Шляху chain
- each package must be independently validated before the next mutation
- canonical Quest Engine and NPC model are content-independent

Remaining question: Define five exact package manifests 1-10, 11-20, 21-30, 31-40 and 41-50 plus validators for IDs, predecessor chain, levels, objective schema, NPC/location references, quest items, rewards, localization and duplicate content.

### QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE

Confirmed:

- quest 49 forced encounter and turn-in were manually accepted in V1
- quest 50 ends the Початок Шляху story by talking to the Elder
- a known V1 presentation defect hides 1/1 progress after the leader victory until quest 49 turn-in
- the defect is presentation-only and must be tracked explicitly

Remaining question: Resolve the exact quest 49 and 50 records, NPCs, objective transitions and completion flags; decide from V1 evidence whether V2 must preserve or correct the hidden 1/1 presentation nuance, without changing accepted combat or completion semantics.

No production mutation, canonical reference edit, quest migration, reward change, database access or runtime wiring is authorized.

## Next patch

`patch_21_13_4b_resolve_story_content_1_50_parity.py`
