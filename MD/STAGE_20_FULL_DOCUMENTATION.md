# ROM Stage 20 — Full Technical Documentation

## 1. Closure metadata

- Generated: `2026-10-13T23:16:12.178848+00:00`
- Stage 20.7.1 regression: `GO`
- Stage 20.7.2 manual acceptance: `ACCEPTED`
- Final Stage 20 status: `CLOSED`
- Critical gaps: `0`
- High gaps: `0`
- Production code changed by closure: `NO`
- Production database opened or changed by closure: `NO`

This document is the canonical Stage 20 technical dump. Later defects do not reopen Stage 20 automatically. They must be handled as separate audit/mutation stages with their own rollback, reports, tests and manual acceptance.

## 2. Stage structure and final decisions

### Stage 20.1 — baseline, owner mapping and planning

Stage 20.1 established the authoritative owner map, runtime baselines, economic baselines and decision gates used by later Stage 20 work. It also preserved Stage 19 story, localization, event namespace and quest exact-once invariants.

### Stage 20.2 — class combat foundation

Final status: `ACCEPTED`.

Implemented and accepted:

- class-specific basic attacks and combat resource routing;
- physical and magical attack ownership;
- Priest healing behavior and regressions;
- class combat messages and damage/healing flow;
- normal, elite and boss compatibility;
- preservation of existing PDEF/MDEF damage semantics;
- maintained smoke and manual evidence.

The accepted stat formulas remain configuration-owned. Core examples preserved by the project include Warrior `STR×1.0 + DEX×0.2`, Knight `STR×1.1 + DEX×0.1`, Scout `STR×0.65 + DEX×0.55`, Rogue `STR×0.4 + DEX×0.8`, Mage MATK `INT×1.05 + WIS×0.15`, Priest MATK `INT×0.9 + WIS×0.3`, and Max MP `100 + level×20 + INT + WIS×4`.

### Stage 20.3 — hybrid Mana and economy integration

Final status: `ACCEPTED`.

Accepted contracts:

- one canonical mana-spend pipeline;
- PvE, PvP and simulator parity;
- post-combat Mana regeneration and floor contracts;
- active, inactive and insufficient-Mana paths;
- no duplicate Mana deduction;
- maintained economy compatibility;
- accepted regression and manual evidence.

The accepted post-combat model includes `30%` regeneration and a `50%` floor where applicable. Any future change must update PvE, PvP, simulator and UI together.

### Stage 20.4 — general economy

Final status: `ACCEPTED`.

#### Daily rewards

- Firius Tokens per successful daily claim: `3`.
- Small health potions: item `401 ×3`.
- Reward is exact-once.
- Existing token balances are not reduced or normalized retroactively.
- Preview, claim result and token item description use the canonical quantity.

#### Level-up gold

The old `level × 8 / milestone × 12` formula was replaced by a frozen matrix based on `10%` of expected same-level normal-mob combat income. Values are shown with exactly two decimals:

- reached level 2: `0.45`
- reached level 3: `1.43`
- reached level 4: `4.30`
- reached level 5: `11.98`
- reached level 6: `34.40`
- reached level 7: `69.58`
- reached level 8: `130.73`
- reached level 9: `255.74`
- reached level 10: `479.19`
- reached level 11: `881.25`

There is no special milestone gold multiplier. Milestone item rewards remain unchanged. Existing balances and already-claimed ledger rows are not recalculated.

#### Potion prices

Stage 20.4.4 was closed as `NOT_REQUIRED`. Current buy/sell prices remain:

- small HP: `5.00 / 1.00`
- medium HP: `15.00 / 3.00`
- small MP: `4.00 / 0.80`
- medium MP: `12.50 / 2.50`

Simulator instrumentation distinguishes HP/MP potions, owned/dropped purchases and potion spending. The owner decision was to avoid further long simulations and retain current prices.

#### Guild creation

- minimum level: `3`;
- creation cost: `50.00` gold;
- initial member limit: `10`;
- price and limit are shown at the first step and final confirmation;
- debit remains atomic and conditional;
- existing guilds and historical logs are not modified.

### Stage 20.5 — Premium and admin crystals

Final status: `ACCEPTED`.

#### Premium benefits

- `+25%` experience from normal, elite and boss victories;
- `+25%` combat gold from normal, elite and boss victories;
- unavailable for quests, contracts, sales, auction, admin operations, refunds and guild rewards;
- Premium loot modifier remains `NOT IMPLEMENTED / UNDECIDED`;
- user-facing terminology uses `досвід`, not `EXP`;
- expiration is stored in UTC and displayed as `DD.MM.YYYY HH:MM за Києвом` using `Europe/Kyiv`.

#### Premium prices

- 15 days: `100` crystals;
- 30 days: `180` crystals.

Other crystal prices remain:

- Sphere of a New Path: `150`;
- Name Rune: `50`;
- Rune of Success: `35`;
- Perfect Extractor: `20`;
- bag `60→80`: `75`;
- bag `80→100`: `150`.

Purchases remain atomic and idempotent. Active duration stacks from the later of current expiry and current UTC time. Historical purchases and existing expiration timestamps are not repriced.

#### Admin crystals

The command/menu/wizard flow is operational. The missing `admin_crystal_credit_audit` startup bootstrap was fixed by wiring the idempotent initializer before handler registration.

Accepted behavior:

- authorized credit and debit;
- clamped debit without negative balance;
- idempotent replay;
- recipient notification;
- persistent history and detail view;
- startup-safe table and index creation;
- unauthorized administrator rejection.

### Stage 20.6 — travel presentation and generated equipment

Final status: `ACCEPTED`.

#### Travel

Canonical graph:

- `Місто ↔ Початок Шляху ↔ Темний Бір`;
- 3 nodes, 4 route directions;
- duration: `20 seconds`;
- separate preview, active and arrival text;
- enriched City map information;
- restart recovery preserved;
- unknown locations fail closed as `Невідома місцевість`;
- raw technical IDs are not shown.

#### Equipment generation

Final source-aware policy:

**Base shop**

- identity is suitable for the buyer class;
- primary stats are suitable for the buyer class;
- shop ring/necklace stats are class-aware;
- preview is promoted as the same snapshot without reroll.

**Mob loot**

- weapon/off-hand stats are based on item subtype identity;
- armor stats are based on armor type identity;
- dropped jewelry uses a universal random `STR/DEX/INT/WIS/STA` pool;
- recipient class does not rewrite mob-loot stats;
- `class_aware_chance` controls suitability of identity only.

**Forced-slot generation**

- `armor_type` is always initialized before identity resolution;
- unknown subtype/armor type fails closed before persistence.

**Shoulders**

- common: PDEF + MDEF + base primary stat;
- uncommon/rare/epic: PDEF + MDEF + base primary stat + rarity stat chunks;
- the temporary defense-only interpretation from Stage 20.6.5c is superseded by Stage 20.6.5d.

Existing items were not migrated or rerolled.

### Stage 20.7 — regression, manual acceptance and closure

- Stage 20.7.1: full regression `GO`, 0 critical gaps, 0 high gaps;
- maintained suites: `16 PASS`;
- historical suites: `4 SUPERSEDED` with replacement evidence;
- Stage 20.7.2: owner manual acceptance `ACCEPTED`, no current remarks;
- Stage 20.7.3: documentation and final closure.

## 3. Database and persistence contracts

Stage 20 preserves the following principles:

- schema bootstrap is idempotent;
- wallet and reward ledgers preserve exact-once/idempotency semantics;
- admin crystal audit history is persistent;
- active travel persists across restart;
- shop preview promotion does not reroll equipment;
- no Stage 20 closure operation rewrites existing items or balances;
- WAL/SHM files are never deleted, cleared or used as rollback material;
- production DB validation uses isolated snapshots where required;
- final regression passed `quick_check` and foreign-key checks.

## 4. Stage 19 invariants retained

Stage 20 preserves:

- story quests 1–100 and sequential story-chain contracts;
- localized human location names `Початок Шляху` and `Темний Бір`;
- the term `розділ`, not `глава`;
- canonical location-name resolver usage;
- quest-item and reward exact-once behavior;
- event item namespace `4000–9999` with permanent 25-ID blocks;
- no presentation of raw `start_path` or `dark_forest` IDs;
- accepted Stage 19 manual story evidence.

## 5. Superseded decisions and tools

- Stage 20.6.4 recipient-class STRICT policy was superseded by Stage 20.6.4a identity-aware mob-loot policy plus source-specific shop policy.
- Stage 20.6.5 initial shop-equals-loot implementation was superseded by Stage 20.6.5b.
- Stage 20.6.5b temporary shoulder rarity-loop exception was superseded by Stage 20.6.5c.
- Stage 20.6.5c defense-only shoulders interpretation was superseded by Stage 20.6.5d.
- The regression registry records four historical tools as superseded and requires approved replacement evidence.

## 6. Testing and acceptance evidence

- acceptance reports exist for Stages 20.2, 20.3, 20.4, 20.5 and 20.6;
- full Stage 20 regression returned `GO`;
- production owners remained unchanged during regression and closure;
- DB snapshot integrity passed;
- manual evidence covered class combat, Mana/economy, Premium combat rewards, admin crystal credit/debit/history, travel UI/recovery, shop/equipment behavior and shoulders.

## 7. Known nuances and accepted limitations

- Premium loot bonus is intentionally undecided and not implemented.
- Equipment identity may be unsuitable for the receiving class in unrestricted mob-loot paths; stats remain coherent with item identity.
- Dropped jewelry is intentionally universal and may be unsuitable for the receiver.
- Future level-up gold values above reached level 11 require a new audited matrix extension.
- Potion price decision was owner-approved without additional long simulations.
- Later defects must be handled in separate stages and do not silently rewrite this closure decision.

## 8. Operational rules after closure

- New mutation patches require backup before mutation and automatic rollback on mandatory-check failure.
- Reports belong in `reports`, executable checks in `tools`, documentation in `MD`.
- `ROM_FULL_DUMP.txt` may be dirty but must not be staged by patches.
- `game.db-wal` and `game.db-shm` must never be deleted, truncated or forcibly manipulated.
- New or changed complex logic must include meaningful comments or docstrings.

## 9. Stage 20 Git commit registry

- `cb59b0b844cdbbba5c85fd511b2ce54a5b0c0349` — Stage 20.1.1: audit Stage 20 change requests
- `1b919ab2e1f603bc674ccac3fbc694825722b611` — Stage 20.1.2: audit gold economy levels 1-10
- `560208180b2c530f61d0aa71cf9278bc3b9cfa43` — Stage 20.2.1: audit class-aware basic attack
- `2482c3a8e0f089fbf4e40f27fb230ef87deb0251` — Stage 20.2.2: implement class basic attack type
- `5e85116703aa1411c58d740604c96b819f2c9199` — Stage 20.2.2a: fix magical basic attack stat routing
- `06562b7f48cce581e2241ce16df3decde0f9037d` — Stage 20.2.3: apply PvP and simulator basic attack parity
- `d1fbe300ab9b6385f1b0b77e2ee35354676c1229` — Stage 20.2.4: audit Priest healing duration and cooldown
- `7ba81d091e1adee3be1cdda9afe0d05c0afc0fa5` — Stage 20.2.5: consolidate Priest healing lifecycle
- `161897a2a6d856c3ee52450d120ee572eb092da7` — Stage 20.2.5a: finalize Priest three-heal lifecycle
- `b830f4f11cb761a162bc7c539e77998c9e14be70` — Stage 20.2.5b: fix Priest description and cooldown display
- `fb2720354e2f64f0682aae5b4c44b34a49ce2bf8` — Stage 20.2.6: audit class combat baseline acceptance
- `9699e3ad6aa06d80cbcf533ba0a871a8ca2e64ac` — Stage 20.3.1: audit complete mana pipeline
- `8efbb0cb565462c37193fd2ef0dab7805a1e672b` — Stage 20.3.2: create canonical mana policy
- `4dd23c2c030a1547307429c1f49db05e8bd91231` — Stage 20.3.3: extend Mana skill catalog
- `972280f3efa1d5e545af85e43ca40fb92ce555dd` — Stage 20.3.4: integrate canonical Mana cost into PvE
- `7c0b808acb0ba3752bf8a0b65b7046e080406fe3` — Stage 20.3.4a: fix dynamic Mana skill descriptions
- `d3c2fc63d9d3fd380e3d09f50560321624b3d8a8` — Stage 20.3.4b: finalize dynamic Mana skill descriptions
- `69a0602a4cc4c0f2f19004d18de3ffb32971830a` — Stage 20.3.5: apply 50 percent post-combat Mana floor
- `f8e6107d56921d65a6aaf72ce04d242348b196b0` — Stage 20.3.6: integrate canonical Mana policy into PvP
- `dc2c3ca817f383db3d3d31ee32415535bc6243a3` — Stage 20.3.7: audit simulator Mana pipeline
- `094c7a1abe42dcdf968d8a61d0de21585c614093` — Stage 20.3.7: integrate mana parity into simulator
- `a8babda25bc98f89b9235d3425a50c9d7de1247e` — Stage 20.3.8: consolidate legacy Mana paths
- `aeb94486f23ec281c153fff94fb6447e69350b52` — Stage 20.3.9: accept hybrid Mana economy
- `6cf2a312a99196c5520058008f9105d2bc0d632b` — Stage 20.4.1: audit daily Firius Token reward
- `eca246467bce6aaf55150e632bd709d5ff7b064e` — Stage 20.4.1a: reduce daily Firius Token reward to 3
- `f5748e639788147742635dbadc9044cb031897d1` — Stage 20.4.1b: fix Firius Token item description
- `979bea3fd786a81768f4015e595814c50837393f` — Stage 20.4.2: audit level-up gold rebalance
- `92ceba70b88a85663f39cb720906d33dd8129524` — Stage 20.4.2a: audit level-up gold as 10 percent combat income
- `e5af88bd59d487303f85d0a58b808681e97b8658` — Stage 20.4.2b: apply combat-income-based level-up gold
- `d33453bcd2fa54ce96b0318c614140604708bb0a` — Stage 20.4.2c: fix level-up gold decimal presentation
- `896591b06be22f2db25129ef2713ae7423d7f964` — Stage 20.4.3: audit potion affordability after mana changes
- `79b1773ac93d977e94518ad53eaccb4ba5fe03c5` — Stage 20.4.3a: instrument simulator potion affordability
- `50449f30b59f2b3eb16d334b61899f42730a7ce5` — Stage 20.4.3b: repeat potion affordability audit through level 5
- `cc1555507c87cd69c23863250db04802fa834d58` — Stage 20.4.5: audit level-3 guild creation affordability
- `cdf76e8bbb4f7cdac60611b8f2c3ec28586c9e02` — Stage 20.4.6: reduce guild creation cost to 50 gold
- `47003f582fbc58e0f0e8c46ccb4c883617fd6c6e` — Stage 20.4.6a: show guild creation cost at start
- `3fc4f9b47bdb7b9ee2dab3a9ead7b8bd6d9bda4f` — Stage 20.4.7: accept general economy changes
- `dfd23e91ad8c2492e75e89ef5c7f01290bc65442` — Stage 20.5.1: audit Premium modifiers
- `cbe45ca87f59f018e7b96e8262b6a99c1679769b` — Stage 20.5.2: add 25 percent Premium combat gold
- `79c1c4f0841d242df5830dc00e0ce5e5da357fdc` — Stage 20.5.2a: unify Premium experience and gold UI
- `1a4abcbfaa7f8d1e6fb5f3fb721d85a47955eeb5` — Stage 20.5.2b: unify Premium expiration time in Kyiv
- `3cc78dd3628a9659d4aac88d99ddd1e01764bfcb` — Stage 20.5.2c: fix Premium expiration formatter runtime
- `54487f853680998552d88b846503f659d31bf749` — Stage 20.5.3: audit crystal shop prices
- `abebc3f5c6f0622c0ef059068ec93adac49d5db9` — Stage 20.5.4: update Premium prices to 100 and 180 crystals
- `af579a5426bf03e15532ee706b5528fc863a5250` — Stage 20.5.5: audit admin crystal schema bootstrap
- `ad6c07b99b29aad33a8f0b677d6e37a10fdb8df2` — Stage 20.5.6: wire admin crystal schema startup
- `712d71dff2db87e428a2a37bded904be10dcccb1` — Stage 20.5.7: accept Premium and admin crystals
- `a9773dfc627d0bd8c1189a09544984f5e7a27198` — Stage 20.6.1: audit travel presentation
- `c49c26aad4dcb6dd35ef0299d6a0c0bb61a2a9af` — Stage 20.6.2: apply canonical travel presentation
- `e8f53587a414ab5963450645263890b54c0be108` — Stage 20.6.3: audit class-aware equipment generation
- `b496faf742d4550c8c02f9f1a4817143d27fbf22` — Stage 20.6.4: approve strict primary-stat equipment policy
- `68d79bcbb29815dc694891924542cedc3afc20d5` — Stage 20.6.4a: approve identity-aware equipment stat policy
- `4733acc247f26e8c5515f54c21fb83b87876fe9a` — Stage 20.6.5: implement identity-aware equipment stats
- `ba1fc548e55ec7e5df7eb135bc9d6210fa567737` — Stage 20.6.5a: audit forced-slot armor type routing
- `295db352a703572af34415d0945eb49964ea9e6b` — Stage 20.6.5b: fix forced-slot and shop class policy
- `55893d1ae4b4c1b8da3cf578fd7155a79cad6762` — Stage 20.6.5c: localize defense-only shoulders policy
- `9afe044ad1ae448078201f2d34da309b437c1f0c` — Stage 20.6.5d: restore shoulders primary stats
- `7b51ca9e8f71193e36c66b9708846f2431a7d6c9` — Stage 20.6.6: accept travel and equipment generation
- `1e8314d3d32ed5bb6861361c156e51d3acc1a8fb` — Stage 20.7.1: full Stage 20 regression

## 10. Stage 20 machine-report registry

- `reports/stage_20_1_1_change_requests_audit.json` — stage `20.1.1`, status `PASS`, decision `GO`
- `reports/stage_20_1_2_gold_economy_levels_1_10.json` — stage `20.1.2`, status `PASS`, decision `CONDITIONAL_GO`
- `reports/stage_20_2_1_class_aware_basic_attack.json` — stage `None`, status `PASS`, decision `CONDITIONAL_GO`
- `reports/stage_20_2_2_class_basic_attack_type.json` — stage `20.2.2`, status `PASS`, decision `None`
- `reports/stage_20_2_2a_magical_basic_attack_stat_routing.json` — stage `20.2.2a`, status `PASS`, decision `None`
- `reports/stage_20_2_3_pvp_simulator_basic_attack_parity.json` — stage `20.2.3`, status `PASS`, decision `None`
- `reports/stage_20_2_4_priest_healing_duration_cooldown.json` — stage `20.2.4`, status `PASS`, decision `CONDITIONAL_GO`
- `reports/stage_20_2_5_priest_healing_lifecycle.json` — stage `20.2.5`, status `PASS`, decision `None`
- `reports/stage_20_2_5a_priest_three_heals.json` — stage `20.2.5a`, status `PASS`, decision `None`
- `reports/stage_20_2_5b_priest_description_and_cooldown.json` — stage `20.2.5b`, status `PASS`, decision `None`
- `reports/stage_20_2_6_class_combat_acceptance.json` — stage `20.2.6`, status `PASS`, decision `None`
- `reports/stage_20_3_1_complete_mana_pipeline_audit.json` — stage `20.3.1`, status `PASS`, decision `None`
- `reports/stage_20_3_2_canonical_mana_policy.json` — stage `20.3.2`, status `PASS`, decision `None`
- `reports/stage_20_3_3_mana_skill_catalog.json` — stage `20.3.3`, status `PASS`, decision `None`
- `reports/stage_20_3_4_pve_mana_cost_integration.json` — stage `20.3.4`, status `PASS`, decision `None`
- `reports/stage_20_3_4a_dynamic_mana_skill_descriptions.json` — stage `20.3.4a`, status `PASS`, decision `None`
- `reports/stage_20_3_4b_finalize_dynamic_mana_skill_descriptions.json` — stage `20.3.4b`, status `PASS`, decision `None`
- `reports/stage_20_3_5_post_combat_mana_floor.json` — stage `20.3.5`, status `PASS`, decision `None`
- `reports/stage_20_3_6_pvp_mana_policy.json` — stage `20.3.6`, status `PASS`, decision `None`
- `reports/stage_20_3_7_simulator_mana_parity.json` — stage `20.3.7`, status `PASS`, decision `None`
- `reports/stage_20_3_7_simulator_mana_pipeline_audit.json` — stage `20.3.7`, status `PASS`, decision `GO`
- `reports/stage_20_3_8_legacy_mana_consolidation.json` — stage `20.3.8`, status `PASS`, decision `None`
- `reports/stage_20_3_9_hybrid_mana_economy_acceptance.json` — stage `20.3.9`, status `PASS`, decision `ACCEPTED`
- `reports/stage_20_4_1_daily_firius_token_reward_audit.json` — stage `20.4.1`, status `PASS`, decision `GO`
- `reports/stage_20_4_1a_daily_firius_token_reward.json` — stage `20.4.1a`, status `PASS`, decision `None`
- `reports/stage_20_4_1b_firius_token_item_description.json` — stage `20.4.1b`, status `PASS`, decision `None`
- `reports/stage_20_4_2_level_up_gold_rebalance_audit.json` — stage `20.4.2`, status `PASS`, decision `VALUES_APPROVAL_REQUIRED`
- `reports/stage_20_4_2a_level_up_gold_10_percent_combat_income_audit.json` — stage `20.4.2a`, status `PASS`, decision `POLICY_APPROVAL_REQUIRED`
- `reports/stage_20_4_2b_combat_income_based_level_up_gold.json` — stage `20.4.2b`, status `PASS`, decision `None`
- `reports/stage_20_4_2c_level_up_gold_decimal_presentation.json` — stage `20.4.2c`, status `PASS`, decision `None`
- `reports/stage_20_4_3_potion_affordability_audit.json` — stage `20.4.3`, status `PASS`, decision `NO_PRICE_CHANGE_INSTRUMENTATION_REQUIRED`
- `reports/stage_20_4_3a_simulator_potion_affordability_instrumentation.json` — stage `20.4.3a`, status `PASS`, decision `None`
- `reports/stage_20_4_3b_potion_affordability_level_5_audit.json` — stage `20.4.3b`, status `PASS`, decision `PRICE_REVIEW_REQUIRED_LEVEL_1_5`
- `reports/stage_20_4_5_level_3_guild_creation_affordability.json` — stage `20.4.5`, status `PASS`, decision `REDUCE_GUILD_COST_TO_50`
- `reports/stage_20_4_6_guild_creation_cost_50.json` — stage `20.4.6`, status `PASS`, decision `None`
- `reports/stage_20_4_6a_guild_creation_cost_at_start.json` — stage `20.4.6a`, status `PASS`, decision `None`
- `reports/stage_20_4_7_general_economy_acceptance.json` — stage `20.4.7`, status `PASS`, decision `ACCEPTED`
- `reports/stage_20_5_1_premium_modifiers_audit.json` — stage `20.5.1`, status `PASS`, decision `GO_EXACT_SCOPE_RECORDED_COMBAT_GOLD_GAP`
- `reports/stage_20_5_2_premium_combat_gold_25_percent.json` — stage `20.5.2`, status `PASS`, decision `None`
- `reports/stage_20_5_2a_premium_experience_gold_ui.json` — stage `20.5.2a`, status `PASS`, decision `None`
- `reports/stage_20_5_2b_premium_expiration_time_kyiv.json` — stage `20.5.2b`, status `PASS`, decision `None`
- `reports/stage_20_5_2c_premium_expiration_formatter_runtime.json` — stage `20.5.2c`, status `PASS`, decision `None`
- `reports/stage_20_5_3_crystal_shop_prices_audit.json` — stage `20.5.3`, status `PASS`, decision `OWNER_PRICE_SELECTION_REQUIRED_FOR_20_5_4`
- `reports/stage_20_5_4_premium_prices_100_180.json` — stage `20.5.4`, status `PASS`, decision `None`
- `reports/stage_20_5_5_admin_crystals_command_audit.json` — stage `None`, status `PASS`, decision `ROOT_CAUSE_FOUND`
- `reports/stage_20_5_6_admin_crystal_schema_startup.json` — stage `20.5.6`, status `PASS`, decision `None`
- `reports/stage_20_5_7_premium_admin_crystals_acceptance.json` — stage `None`, status `PASS`, decision `STAGE_20_5_ACCEPTED`
- `reports/stage_20_6_1_travel_presentation_audit.json` — stage `None`, status `PASS`, decision `CANONICAL_TEXT_METADATA_DESIGN_READY`
- `reports/stage_20_6_2_travel_presentation.json` — stage `20.6.2`, status `PASS`, decision `None`
- `reports/stage_20_6_3_class_aware_equipment_audit.json` — stage `None`, status `PASS`, decision `STRICT_WEIGHTED_OPTIONS_AND_ROOT_CAUSE_READY`
- `reports/stage_20_6_4_strict_primary_stats_policy.json` — stage `20.6.4`, status `PASS`, decision `STRICT_PRIMARY_STATS_APPROVED`
- `reports/stage_20_6_4a_identity_aware_equipment_policy.json` — stage `20.6.4a`, status `PASS`, decision `IDENTITY_AWARE_EQUIPMENT_STATS_APPROVED`
- `reports/stage_20_6_5_identity_aware_equipment_stats.json` — stage `20.6.5`, status `PASS`, decision `None`
- `reports/stage_20_6_5a_forced_slot_armor_type_audit.json` — stage `None`, status `PASS`, decision `FORCED_SLOT_ARMOR_TYPE_ROOT_CAUSE_FOUND`
- `reports/stage_20_6_5b_forced_slot_shop_class_policy.json` — stage `20.6.5b`, status `PASS`, decision `None`
- `reports/stage_20_6_5c_shoulders_stat_policy.json` — stage `20.6.5c`, status `PASS`, decision `None`
- `reports/stage_20_6_5d_shoulders_primary_stats.json` — stage `20.6.5d`, status `PASS`, decision `None`
- `reports/stage_20_6_6_travel_equipment_acceptance.json` — stage `None`, status `PASS`, decision `STAGE_20_6_ACCEPTED`
- `reports/stage_20_7_1_full_regression.json` — stage `None`, status `PASS`, decision `CLOSURE_READINESS_GO`

## 11. Final closure statement

Stage 20 is closed with automated regression `GO`, manual acceptance `ACCEPTED`, zero critical gaps and zero high gaps. This document is the final technical baseline for subsequent ROM work.
