# Seasonal Event Template

Copy this directory to a new package such as `events/<event_key>/`.

Before registration:

1. Replace `_template` lifecycle metadata with a stable `EVENT_KEY`.
2. Set timezone-aware `START_AT` and `END_AT`.
3. Keep combat formulas in canonical systems. Event modules provide data only.
4. Define item IDs only after the event static namespace is allocated.
5. Keep item definitions resolvable after the event ends.
6. Recheck active state in every callback and before every mutation.
7. Do not add database writes to `mobs.py`, `bosses.py`, `items.py`, or `drops.py`.
8. Do not register this template in `EVENT_MODULES`.
