# Stage 21.8.6a - Refined status effects contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **25**
- Review-required rows: **4**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `pve`: `handlers/combat.py`
- `boss`: `systems/boss_system.py`
- `pvp`: `systems/pvp_round_engine.py`
- `simulator`: `systems/simulation/pve_battle.py`
- `priest_policy`: `data/priest_healing_policy.py`
- `pvp_presentation`: `systems/pvp_combat_log.py`

## Contract matrix

- `PVE_EFFECT_CONTAINER`: **V1_CONFIRMED** - PvE combat state owns separate enemy/player effect mappings.
- `PVE_ENEMY_EFFECT_APPLY_REFRESH`: **V1_CONFIRMED** - Enemy effects use the implemented V1 stronger/longer replacement policy; the helper does not carry a generic refresh_policy field.
- `PVE_PLAYER_EFFECT_APPLY`: **V1_CONFIRMED** - Player-target effects are inserted by the canonical PvE helper.
- `PVE_EXPLICIT_REMOVAL`: **V1_CONFIRMED** - PvE enemy-effect removal is explicit.
- `PVE_PLAYER_TURN_START`: **V1_CONFIRMED** - Player turn-start processing owns applicable ticks/decrement/expiration.
- `PVE_ENEMY_TURN_START`: **V1_CONFIRMED** - Enemy turn-start processing owns applicable ticks/decrement/expiration.
- `PVE_SHIELD_ABSORB`: **V1_CONFIRMED** - PvE shield prevention is a dedicated consumption layer.
- `PVE_SKILL_EFFECT_DISPATCH`: **V1_CONFIRMED** - PvE skill special-effect dispatch remains a V1 owner boundary.
- `PVE_EFFECT_PRESENTATION`: **V1_CONFIRMED** - PvE effect presentation is separate from mutation helpers.
- `PVE_VICTORY_HOT_ROLLBACK`: **V1_CONFIRMED** - V1 explicitly compensates a turn-start HoT when victory terminates the action.
- `PRIEST_HEAL_IDENTITY`: **V1_CONFIRMED** - Priest HoT identity is canonical policy data.
- `PRIEST_HEAL_1_PLUS_2`: **V1_CONFIRMED** - Priest healing is one immediate heal plus two duration ticks.
- `PRIEST_HEAL_REAPPLICATION`: **V1_CONFIRMED** - Priest HoT reapplication policy is replace.
- `PRIEST_HEAL_EFFECT_BUILDER`: **V1_CONFIRMED** - Canonical builder emits the V1 HoT payload.
- `BOSS_EFFECT_OWNER`: **V1_CONFIRMED** - Boss action effects are owned by boss_system.
- `BOSS_PLAYER_EFFECT_INSTRUCTION`: **V1_CONFIRMED** - Boss-to-player application instruction is explicit.
- `BOSS_BLEED_TICK`: **V1_CONFIRMED** - Boss bleed damage/decrement/expiration is processed separately.
- `BOSS_TEMP_BUFF_TICK`: **V1_CONFIRMED** - Boss temporary buffs have a dedicated duration tick.
- `PVP_TURN_START`: **V1_CONFIRMED** - PvP start-of-round tick and expiration ordering is explicit.
- `PVP_REPLACE_POLICY`: **V1_CONFIRMED** - PvP applies same-key effects by replacement.
- `PVP_SPECIAL_EFFECTS`: **V1_CONFIRMED** - PvP special-effect creation is explicit.
- `PVP_SHIELD_ABSORB`: **V1_CONFIRMED** - PvP shield consumption is a dedicated layer.
- `PVP_EFFECT_PRESENTATION`: **V1_CONFIRMED** - PvP log rendering consumes effect events without owning mutation.
- `SIMULATOR_TURN_START`: **V1_CONFIRMED** - Exact PvE simulator has an independent start-of-turn effect implementation.
- `SIMULATOR_EFFECT_APPLY`: **V1_CONFIRMED** - Exact PvE simulator has an independent effect application implementation.
- `CROSS_CONTEXT_PARITY`: **REVIEW_REQUIRED** - PvE, PvP, boss and simulator owners are distributed; exact common/intentional differences require resolution.
- `GENERAL_RESIST_IMMUNITY`: **REVIEW_REQUIRED** - Discovery did not establish one authoritative general resist/immunity contract for all effects.
- `EFFECT_PERSISTENCE_RESTART`: **REVIEW_REQUIRED** - Discovery did not establish one authoritative persistence/restart contract across transient combat contexts.
- `FAILURE_ATOMICITY`: **REVIEW_REQUIRED** - Distributed effect mutation paths need an explicit cross-context no-partial-mutation decision before V2 implementation.

## Unresolved contracts

- `CROSS_CONTEXT_PARITY`
- `GENERAL_RESIST_IMMUNITY`
- `EFFECT_PERSISTENCE_RESTART`
- `FAILURE_ATOMICITY`

Implementation remains unauthorized until these cross-context contracts are resolved from V1 evidence without inventing policy.
