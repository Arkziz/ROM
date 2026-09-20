# Stage 18.30.5c

Simulation-only restoration of canonical player stat parity.

`systems/simulation/combat_actor_stats.py` now delegates Max HP, physical attack, magical attack, PDEF, and MDEF to production stat owners. Existing simulation state assembly remains responsible only for active equipment, rune contributions, durability suppression, armor refine percentage, and refined weapon damage.

Current HP semantics are preserved: a higher maximum does not heal the character, while current HP is clamped when it exceeds a reduced maximum. Production gameplay code and database files are not modified.
