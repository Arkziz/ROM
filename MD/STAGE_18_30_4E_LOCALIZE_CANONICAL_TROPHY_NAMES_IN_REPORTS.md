# Stage 18.30.4e

Simulation-only reporting fix. Canonical trophy names are resolved read-only from the existing `items` catalog in `game.db`. No trophy names are copied or hard-coded into simulation code.

Production mob definitions, drop code, inventory code, item data and database content remain unchanged. The read-only SQLite URI (`mode=ro`) prevents report generation from mutating the database.

The existing three-file simulation report contract is unchanged.
