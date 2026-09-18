# ROM Stage 18.29.4l: Test Event Mob Primary-Stat Template

The active test event now creates its mob from a copied canonical ordinary template selected for the current player level and hunt location. The ordinary template remains the owner of all ten primary-stat ranges and standard reward defaults. The event overlay changes only the event display name, attack type, current level and current location before calling the existing `build_mob()` once.

This resolves the observed `KeyError: level` and `KeyError: str_min` without adding separate event combat formulas or mutating shared templates. The locally edited `events/test_event_2026/config.py` schedule is preserved and excluded from this commit.
