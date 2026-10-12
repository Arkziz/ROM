# Stage 20.5.2c — Premium Expiration Formatter Runtime Fix

The Kyiv formatter is now self-contained and accepts ISO strings, `Z` strings, timezone-aware `datetime` values and naive `datetime` values. Naive values are interpreted as canonical UTC. Both Premium detail and account handlers use the same implementation.

UTC storage, expiration semantics, Premium duration, formulas, tariffs and database are unchanged.
