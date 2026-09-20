# Stage 18.30.5k

Adds the maintained final simulator acceptance gate without changing gameplay or reporting owners.

The gate validates JSON/XLSX parity, progression and encounter conservation, loot and potion conservation, target completion, final equipment instance/refinement/durability/rune parity, economy reconciliation, workbook structure/formulas, the two-output reporting contract, the 40% potion threshold, the 25% pre-hunt wait threshold, death durability wear, and the inclusive 15% repair boundary.

The patch automatically runs the gate against the existing Scout 1→2 seed 3 JSON/XLSX pair before committing. After success, the next action is the long Scout 1→10 seed 3 simulation followed by this same gate against its two reports.
