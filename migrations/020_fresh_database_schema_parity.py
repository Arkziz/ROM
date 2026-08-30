# -*- coding: utf-8 -*-
"""Stage 18.1.0-a.0-b: non-ambiguous fresh-schema parity contracts."""


def _columns(conn, table):
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _add_column(conn, table, column, declaration):
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


def up(conn):
    tables = {str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if "inventory" not in tables or "items" not in tables:
        raise RuntimeError("base tables inventory/items must exist before migration 020")

    _add_column(conn, "inventory", "refine_level", "INTEGER DEFAULT 0")
    _add_column(conn, "items", "item_subtype", "TEXT DEFAULT ''")
    _add_column(conn, "items", "armor_type", "TEXT DEFAULT ''")
    _add_column(conn, "items", "weapon_min_damage", "INTEGER DEFAULT 0")
    _add_column(conn, "items", "weapon_max_damage", "INTEGER DEFAULT 0")
    _add_column(conn, "items", "weapon_min_magic_damage", "INTEGER DEFAULT 0")
    _add_column(conn, "items", "weapon_max_magic_damage", "INTEGER DEFAULT 0")
    _add_column(conn, "items", "weapon_attack_type", "TEXT DEFAULT ''")
    _add_column(conn, "items", "shop_preview_owner", "INTEGER DEFAULT NULL")
    _add_column(conn, "items", "shop_preview_price", "INTEGER DEFAULT 0")
    conn.execute("UPDATE inventory SET refine_level=0 WHERE refine_level IS NULL")
    conn.execute("UPDATE items SET shop_preview_price=0 WHERE shop_preview_price IS NULL")
