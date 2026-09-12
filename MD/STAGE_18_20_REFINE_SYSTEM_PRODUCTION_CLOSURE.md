# Stage 18.20: Refine System Production Closure

**Status:** CLOSED
**Manual acceptance:** PASS
**Production mutation in closure:** none
**Refine balance mutation:** none

## Closed defects

- Consecutive attempts in one edited Telegram message no longer reuse the previous operation key.
- A real attempt uses `telegram:refine:<user_id>:<callback_id>`.
- Duplicate delivery of the same callback remains idempotent and never consumes materials twice.
- An idempotent replay is no longer rendered as a failed refine attempt or as a new material consumption.
- Expired or invalid refine callback acknowledgements no longer raise a polling traceback.

## Authoritative ownership

- `systems/refine_system.py` remains the canonical transaction, chance, roll and failure-policy owner.
- `handlers/refine.py` remains the Telegram callback, preview and result-rendering owner.
- No override or parallel refine implementation was introduced.

## Balance preserved

- Weapon and armor refine success tables were not changed.
- Maximum refine levels, failure levels, material costs and refine effects were not changed.
- A Success Rune still guarantees success and consumes one rune together with one Enhancement Stone.

## Manual acceptance

The user confirmed that refinement now works correctly. Consecutive normal attempts can refine to +1 and +2 without closing and reopening the menu. Correct materials are consumed, and Success Rune refinement works as expected.

## Automated verification

- Callback-ID idempotency and duplicate-delivery contracts: PASS.
- Truthful replay rendering: PASS.
- Expired callback-query guard: PASS.
- Python compilation and runtime imports: PASS.
- Canonical transaction and chance contracts: PASS.
- `quick_check=ok`, foreign-key violations=0 and production database unchanged.
- WAL/SHM were not manipulated.

## Historical evidence correction

The Stage 18.20.0 audit document recorded the first report as if the stone had been consumed during the false failure. Subsequent direct observation established that the stone was not consumed because the callback replayed an earlier attempt. This closure records the corrected evidence without rewriting the historical audit artifact.

## Final decision

Stage 18.20 is closed. Further refine changes require a separately identified runtime defect or an explicitly approved balance change.
