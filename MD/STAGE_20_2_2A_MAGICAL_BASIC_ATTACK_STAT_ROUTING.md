# Stage 20.2.2a — magical basic attack stat routing recovery

- Status: **PASS**
- Baseline: `2482c3a8e0f089fbf4e40f27fb230ef87deb0251`

## Root cause

Stage 20.2.2 correctly changed the class attack type, but the two weaponless profile branches still returned `physical_stat_attack` as both `stat_attack` and `display_attack`. Mage and Priest therefore showed a magical attack type while dealing damage from PATK.

## Fix

`get_player_attack_profile()` now resolves `attack_type` and the matching `stat_attack` once before equipment fallbacks. Every weaponless, invalid-weapon and equipped-weapon branch consumes that canonical pair.

## Verification

- Six classes without a weapon: PASS.
- Six classes with an invalid equipped item: PASS.
- Mage/Priest route to mocked MATK 37 instead of PATK 11: PASS.
- Physical classes route to PATK 11: PASS.
- No physical-stat fallback remains in profile payloads: PASS.
- DB integrity read-only: PASS.

## Manual verification

**REQUIRED.** Repeat Mage and Priest weaponless PvE. The combat card must show MATK-derived attack above the historical physical value, damage must exceed the minimum where the formula permits, and MP must remain unchanged.
