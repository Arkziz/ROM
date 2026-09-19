# Stage 18.30.4c

Read-only audit of the complete player-like progression path. It inventories existing canonical mobs by location and level, compares production and simulation candidate pools, probes current selection behavior, traces elite/boss/battle/drop/inventory/equipment systems, and defines the restoration contract.

The audit creates one transferable JSON report in `reports/simulation`. It does not modify `game.db`, WAL/SHM, production modules, mob definitions, or loot definitions.

The following restoration must reuse existing canonical mobs and drops only. It must not create synthetic mobs or a copied loot catalog.
