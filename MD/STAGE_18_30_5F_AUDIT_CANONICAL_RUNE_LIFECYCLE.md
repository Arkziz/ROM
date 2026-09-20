# Stage 18.30.5f

Read-only audit of the canonical rune lifecycle.

The audit validates all 25 rune definitions and item-ID round trips, canonical slot capacities for all ten equipment slots, highest-level selection, quantity consumption, pre-existing sockets, multi-item capacity, unequipped items, zero-durability equipment, counters, and the Scout class-aware preference for DEX over an unrelated equal-level rune.

The audit uses corrected `SimulationInventoryItem(simulation_item_id, item_id, ...)` fixtures and performs all mutations only in memory. Production files, simulation implementation, `game.db`, WAL, and SHM remain unchanged.
