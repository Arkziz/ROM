# Stage 18.30.5b1

Corrected read-only audit for equipment defense, armor/weapon refinement, zero durability, and combat-chance delegation.

Unlike Stage 18.30.5b, canonical PDEF and MDEF receive the fixture item's actual defense values, canonical Max HP receives the actual armor-refine percentage, and weapon damage receives canonical weapon refinement. Zero-durability fixtures verify suppression of item stats, runes, defense, refine bonuses, and weapon damage.

Critical-hit and dodge integration is verified at the effective battle boundary: `pve_battle.py` delegates player attacks and mob attacks through canonical rules backed by `systems.combat_system`, which owns crit and dodge calculations. No production or simulation implementation is changed.
