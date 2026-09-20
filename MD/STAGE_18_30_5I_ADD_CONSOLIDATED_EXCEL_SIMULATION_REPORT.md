# Stage 18.30.5i

Adds a consolidated `.xlsx` report to every class progression simulation while preserving the existing JSON, loot CSV, and equipment JSON reports.

The workbook contains `Summary`, `Final Equipment`, `Loot Lifecycle`, and `Economy`. Final equipment records instance IDs, final refinement, durability, primary/defense/weapon stats, and inserted runes. Economy separates mob gold, item sales, repair cost, calculated final balance, actual final balance, and reconciliation difference.

The reporting layer reloads the already written authoritative main JSON payload and does not mutate gameplay state, RNG, inventory, economy, or the database.
