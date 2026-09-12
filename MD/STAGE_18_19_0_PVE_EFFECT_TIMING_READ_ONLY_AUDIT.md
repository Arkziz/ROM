# Stage 18.19.0: PvE Effect Timing Read-only Audit

**Status:** PASS
**Production mutation:** none

## Scope

The audit compares current PvE effect and cooldown ordering with the existing PvP round semantics. PvP is a behavioral reference only and is not modified.

## Target semantics

- **bleed_dot**: new DOT does not tick on application; first tick occurs after the next full turn.
- **stun**: stun applied by player blocks the nearest enemy action; duration 1 skips exactly one action.
- **lethal_periodic**: lethal tick prevents the target's next action and claims terminal completion once.
- **cooldown**: cooldown N blocks N subsequent owner actions; it is ready on the following action.
- **same_dot_reapply**: do not stack damage; refresh only when new duration is longer.
- **buff_debuff**: stronger replaces weaker; equal strength refreshes duration; weaker does not replace stronger.
- **hot**: no immediate heal; first tick after the next turn; clamp to Max HP.
- **shield**: active immediately and may absorb the nearest incoming attack.
- **duration**: new effect is not decremented in its application phase.
- **scope**: PvE mutation only; PvP is behavioral reference unless a shared layer is proven safe.

## Static comparison

- `has_cooldown_tick`: PvE=`True`, PvP=`True`, equal=`True`.
- `has_periodic_tick`: PvE=`False`, PvP=`True`, equal=`False`.
- `has_stun_skip`: PvE=`False`, PvP=`True`, equal=`False`.
- `has_shield_absorb`: PvE=`True`, PvP=`True`, equal=`True`.
- `has_fresh_marker`: PvE=`False`, PvP=`False`, equal=`True`.
- `has_duration_decrement`: PvE=`False`, PvP=`True`, equal=`False`.
- `has_replace_policy`: PvE=`False`, PvP=`True`, equal=`False`.
- `has_stack_policy`: PvE=`True`, PvP=`False`, equal=`False`.

## Findings

- **HIGH PVE_STUN_TIMELINE_DIFFERS_FROM_PVP**: PvP has explicit stunned-skip semantics while PvE static scan does not show an equivalent phase.
- **HIGH PVE_NO_FRESH_EFFECT_MARKER**: No explicit fresh/applied_turn marker was found to prevent same-turn tick or duration decrement.

## Safety decision

- Do not copy the PvP engine wholesale into PvE.
- Reuse or delegate only pure effect-policy helpers if import direction and behavior are proven safe.
- Keep PvP production unchanged in Stage 18.19.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
