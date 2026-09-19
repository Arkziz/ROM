# Stage 18.30.4d

Simulation-only restoration of canonical mob selection. Production game code and canonical content remain read-only.

The simulator continues to call the existing production-backed `ProgressionProvider.mobs(level)`, which uses production location unlocks and `systems.combat_system.get_available_mobs`. It then performs seeded random selection only inside the simulation from the canonical allowed candidates. Active contract targets retain priority.

No mob definitions, location definitions, combat code, drop code, boss code, database files, or production handlers are modified. Existing canonical mob payloads continue into battle, rewards, central drops, inventory, equipment, runes and city maintenance.

Reports add encounter statistics by mob name, mob level, level delta, attack type, location and candidate-pool size, while preserving the maximum three-file contract.
