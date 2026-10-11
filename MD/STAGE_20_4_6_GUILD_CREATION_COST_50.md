# Stage 20.4.6 — Guild Creation Cost 50 Gold

The canonical guild creation cost is reduced from 100.00 to 50.00 gold following Stage 20.4.5. Minimum access level remains 3 and the initial member limit remains 10.

The existing atomic conditional debit, insufficient-gold rejection, guild creation savepoint, guild log, confirmation UI and returned balance remain on the canonical constant. Existing guilds and historical logs are not modified. No database migration or retroactive debit/credit is performed.

Manual verification is required: level 2 remains blocked; level 3 with 49.99 fails without debit; level 3 with at least 50.00 sees 50.00 in confirmation and successful creation deducts exactly 50.00 once, creates the guild with limit 10, and records the 50.00 creation log.
