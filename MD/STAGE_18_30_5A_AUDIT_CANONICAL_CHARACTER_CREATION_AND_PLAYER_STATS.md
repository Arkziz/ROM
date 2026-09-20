# Stage 18.30.5a

Read-only audit of canonical character creation and initial player statistics.

The audit establishes the canonical owner of starting HP, inventories character creation/class-selection entry points, inspects the read-only `users` schema, and compares the simulation actor against canonical HP for all six classes at levels 1, 2, 5, and 10.

Expected production contract: `data.player_hp.get_starting_max_hp()` returns 130 from `60 + level*20 + stamina*5` at level 1 and STA 10.

This patch does not repair parity. It creates only an audit tool, documentation, and a JSON report. Production files, simulation files, `game.db`, WAL, and SHM remain unchanged.
