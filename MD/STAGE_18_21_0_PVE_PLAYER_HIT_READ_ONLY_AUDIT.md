# Stage 18.21.0: PvE Player Hit/Miss Read-only Audit

**Status:** PASS
**Production mutation:** none

## Direct answer

- Normal PvE player attack has an explicit miss branch: `False`.
- Damaging PvE skills have an explicit miss branch: `False`.
- Enemy attacks can be dodged by the player independently of both findings.

## Scope

Stage 18.21 targets only the player's normal PvE attack. Skills and PvP are audited for comparison but remain unchanged unless separately approved.

## Findings

- **HIGH PVE_NORMAL_ATTACK_HAS_NO_PLAYER_HIT_ROLL**: Normal player attack reaches calculate_player_attack/crit/damage without an explicit player miss or target dodge branch.
- **INFO PVE_DAMAGE_SKILLS_ALSO_HAVE_NO_PLAYER_HIT_ROLL**: Damaging PvE skills use calculate_player_attack and damage scaling, but no explicit player miss/target dodge branch was found.

## Candidate semantics

- Hit roll occurs before crit and damage.
- A miss deals zero damage and applies no hit-dependent effects.
- Existing periodic effects and the enemy action continue normally.
- Candidate formula: 95% at equal DEX, ±0.5% per DEX difference, clamped to 50–99%.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
