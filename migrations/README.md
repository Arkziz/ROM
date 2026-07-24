# ROM migrations

This directory contains database migrations for future schema changes.

## Naming

Use numeric prefixes:

```text
001_base.py
002_equipment.py
003_classes.py
004_refine.py
005_guilds.py
006_auction.py
007_next_feature.py
```

## Migration format

Each migration file should define one function:

```python
def up(conn):
    conn.execute("ALTER TABLE users ADD COLUMN example TEXT DEFAULT ''")
```

or:

```python
def migrate(conn):
    conn.execute("ALTER TABLE users ADD COLUMN example TEXT DEFAULT ''")
```

The runner commits after each successful migration and records it in `schema_migrations`.

## Rule

Future DB schema changes should go here instead of being scattered across `db.py` or handlers.
