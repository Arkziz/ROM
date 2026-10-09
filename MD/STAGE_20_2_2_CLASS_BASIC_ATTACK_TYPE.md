# Stage 20.2.2 — canonical class basic attack type

- Status: **PASS**
- Commit baseline: `560208180b2c530f61d0aa71cf9278bc3b9cfa43`

## Implemented contract

- Warrior, Knight, Scout and Rogue: physical basic attack → PATK → PDEF.
- Mage and Priest: magical basic attack → MATK → MDEF.
- Basic attack resource cost remains zero.
- Unknown classes fail closed.

## Authoritative owner

`systems/stat_system.py` owns `BASIC_ATTACK_TYPE_BY_CLASS` and `resolve_basic_attack_type()`.

`db_modules/player.py::get_player_attack_profile()` consumes the resolver. Handlers continue to consume the existing attack profile and are not expanded.

## Exact production files

- `systems/stat_system.py`
- `db_modules/player.py`
- `tools/verify_stage_20_2_2_class_basic_attack.py`

## Verification

- Future-source AST and compile: PASS.
- Targeted six-class verifier: PASS.
- Unknown-class fail-closed test: PASS.
- PvE profile integration AST: PASS.
- Existing combat handler and damage owners: PASS.
- Live DB integrity: PASS, read-only.
- Production rollback contract: PASS.

## Deferred scope

PvP and simulator canonical-consumer parity remains Stage 20.2.3. Skill attack types, mob attack types and boss attack types are unchanged.

## Manual verification

**REQUIRED.** Test one physical class, Mage and Priest in PvE; confirm the basic attack uses the expected defense layer, consumes no resource, and skills remain unchanged.
