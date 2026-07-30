#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 10.2.0: Rune/Firius canonical data, schema, seed and read contracts."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "10.2.0"
DATA_REL = Path("data/runes.py")
SYSTEM_REL = Path("systems/rune_system.py")
MIGRATION_REL = Path("migrations/010_rune_system_data_model.py")
TEST_REL = Path("tools/smoke_test_rune_data_model.py")
DB_REL = Path("db.py")
MAIN_REL = Path("main.py")

DATA_SOURCE = r'''"""Canonical Rune System data for ROM 10.x."""
from __future__ import annotations

RUNE_STATS = ("STR", "STA", "DEX", "INT", "WIS")
RUNE_LEVELS = (1, 2, 3, 4, 5)
RUNE_LEVEL_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
RUNE_STAT_NAMES = {
    "STR": "Сили",
    "STA": "Витривалості",
    "DEX": "Спритності",
    "INT": "Інтелекту",
    "WIS": "Мудрості",
}
RUNE_SLOT_LIMITS = {
    "main_hand": 2,
    "off_hand": 1,
    "helmet": 1,
    "shoulders": 1,
    "chest": 3,
    "gloves": 1,
    "legs": 2,
    "boots": 1,
    "necklace": 1,
    "ring": 1,
}
RUNE_ITEM_ID_START = 501
RUNE_ITEM_ID_END = 525
FIRIUS_TOKEN_ITEM_ID = 526
RUNE_EXTRACTOR_ITEM_ID = 527
PERFECT_RUNE_EXTRACTOR_ITEM_ID = 528
FIRIUS_TOKENS_PER_DAILY_REWARD = 10
RUNE_FUSION_SOURCE_QUANTITY = 3
RUNE_FUSION_TOKEN_QUANTITY = 1
RUNE_MAX_STACK = 999
FIRIUS_TOKEN_MAX_STACK = 999
EXTRACTOR_MAX_STACK = 999

RUNE_ITEM_DEFINITIONS = {}
RUNE_ITEM_ID_BY_KEY = {}
for stat_index, stat in enumerate(RUNE_STATS):
    for level in RUNE_LEVELS:
        item_id = RUNE_ITEM_ID_START + stat_index * len(RUNE_LEVELS) + level - 1
        definition = {
            "id": item_id,
            "stat": stat,
            "level": level,
            "bonus": level,
            "name": f"💠 Руна {RUNE_STAT_NAMES[stat]} {RUNE_LEVEL_ROMAN[level]}",
            "type": f"rune_{stat.lower()}_{level}",
            "rarity": "common",
            "category": "rune",
            "max_stack": RUNE_MAX_STACK,
            "sell_price": 0.0,
        }
        RUNE_ITEM_DEFINITIONS[item_id] = definition
        RUNE_ITEM_ID_BY_KEY[(stat, level)] = item_id

RUNE_UTILITY_ITEM_DEFINITIONS = {
    FIRIUS_TOKEN_ITEM_ID: {
        "id": FIRIUS_TOKEN_ITEM_ID,
        "name": "🪙 Жетон Фіріуса",
        "type": "firius_token",
        "rarity": "common",
        "category": "material",
        "max_stack": FIRIUS_TOKEN_MAX_STACK,
        "sell_price": 0.0,
    },
    RUNE_EXTRACTOR_ITEM_ID: {
        "id": RUNE_EXTRACTOR_ITEM_ID,
        "name": "🧰 Екстрактор рун",
        "type": "rune_extractor",
        "rarity": "common",
        "category": "material",
        "max_stack": EXTRACTOR_MAX_STACK,
        "sell_price": 0.0,
    },
    PERFECT_RUNE_EXTRACTOR_ITEM_ID: {
        "id": PERFECT_RUNE_EXTRACTOR_ITEM_ID,
        "name": "✨ Досконалий Екстрактор рун",
        "type": "rune_extractor_perfect",
        "rarity": "epic",
        "category": "material",
        "max_stack": EXTRACTOR_MAX_STACK,
        "sell_price": 0.0,
    },
}
ALL_RUNE_SYSTEM_ITEM_DEFINITIONS = {
    **RUNE_ITEM_DEFINITIONS,
    **RUNE_UTILITY_ITEM_DEFINITIONS,
}


def get_rune_definition(item_id):
    try:
        return RUNE_ITEM_DEFINITIONS.get(int(item_id))
    except Exception:
        return None


def get_rune_item_id(stat, level):
    try:
        return RUNE_ITEM_ID_BY_KEY.get((str(stat).strip().upper(), int(level)))
    except Exception:
        return None


def is_rune_item_id(item_id):
    return get_rune_definition(item_id) is not None


def get_rune_slot_limit(slot_key):
    return int(RUNE_SLOT_LIMITS.get(str(slot_key or ""), 0))
'''

MIGRATION_SOURCE = r'''"""ROM 10.2.0: normalized inventory rune sockets."""
from __future__ import annotations


def up(conn):
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_runes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            slot_index INTEGER NOT NULL CHECK(slot_index >= 0),
            rune_item_id INTEGER NOT NULL,
            rune_stat TEXT NOT NULL CHECK(rune_stat IN ('STR','STA','DEX','INT','WIS')),
            rune_level INTEGER NOT NULL CHECK(rune_level BETWEEN 1 AND 5),
            inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(inventory_id, slot_index),
            FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE,
            FOREIGN KEY(rune_item_id) REFERENCES items(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_inventory_id "
        "ON inventory_runes(inventory_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_rune_item_id "
        "ON inventory_runes(rune_item_id)"
    )
'''

SYSTEM_SOURCE = r'''"""Rune System foundation: schema, seed, reads and fusion-selection validation."""
from __future__ import annotations

from data.runes import (
    ALL_RUNE_SYSTEM_ITEM_DEFINITIONS,
    FIRIUS_TOKEN_ITEM_ID,
    FIRIUS_TOKENS_PER_DAILY_REWARD,
    PERFECT_RUNE_EXTRACTOR_ITEM_ID,
    RUNE_EXTRACTOR_ITEM_ID,
    RUNE_FUSION_SOURCE_QUANTITY,
    RUNE_FUSION_TOKEN_QUANTITY,
    RUNE_ITEM_DEFINITIONS,
    RUNE_SLOT_LIMITS,
    get_rune_definition,
    get_rune_item_id,
    get_rune_slot_limit,
    is_rune_item_id,
)


def _db():
    import db
    return db


def init_rune_system():
    """Create the normalized socket table and seed all 28 system items."""
    db = _db()
    conn = db.conn
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_runes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            slot_index INTEGER NOT NULL CHECK(slot_index >= 0),
            rune_item_id INTEGER NOT NULL,
            rune_stat TEXT NOT NULL CHECK(rune_stat IN ('STR','STA','DEX','INT','WIS')),
            rune_level INTEGER NOT NULL CHECK(rune_level BETWEEN 1 AND 5),
            inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(inventory_id, slot_index),
            FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE,
            FOREIGN KEY(rune_item_id) REFERENCES items(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_inventory_id "
        "ON inventory_runes(inventory_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_rune_item_id "
        "ON inventory_runes(rune_item_id)"
    )
    seeded = seed_rune_system_items(commit=False)
    conn.commit()
    return {"success": True, "table": "inventory_runes", "seeded": seeded}


def _item_columns():
    db = _db()
    return {row[1] for row in db.conn.execute("PRAGMA table_info(items)").fetchall()}


def _seed_values(definition):
    values = {
        "id": definition["id"],
        "name": definition["name"],
        "type": definition["type"],
        "rarity": definition["rarity"],
        "category": definition["category"],
        "slot_key": "",
        "weapon_hands": 1,
        "max_stack": definition["max_stack"],
        "sell_price": definition["sell_price"],
        "bonus_str": 0,
        "bonus_dex": 0,
        "bonus_int": 0,
        "bonus_wis": 0,
        "bonus_sta": 0,
        "pdef": 0,
        "mdef": 0,
        "item_level": 1,
        "is_generated": 0,
        "item_subtype": "",
        "armor_type": "",
        "weapon_min_damage": 0,
        "weapon_max_damage": 0,
        "weapon_min_magic_damage": 0,
        "weapon_max_magic_damage": 0,
        "weapon_attack_type": "",
        "shop_preview_owner": None,
        "shop_preview_price": 0,
    }
    return values


def seed_rune_system_items(commit=True):
    """Idempotent seed that refuses semantic ID/type collisions."""
    db = _db()
    columns = _item_columns()
    seeded = 0
    for item_id, definition in ALL_RUNE_SYSTEM_ITEM_DEFINITIONS.items():
        existing = db.conn.execute(
            "SELECT name, type FROM items WHERE id=?", (item_id,)
        ).fetchone()
        if existing and str(existing[1]) != definition["type"]:
            raise RuntimeError(
                f"Rune item ID collision {item_id}: existing={existing}, "
                f"expected_type={definition['type']}"
            )
        values = _seed_values(definition)
        selected = [name for name in values if name in columns]
        placeholders = ", ".join("?" for _ in selected)
        column_sql = ", ".join(selected)
        update_sql = ", ".join(
            f"{name}=excluded.{name}" for name in selected if name != "id"
        )
        db.conn.execute(
            f"INSERT INTO items ({column_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {update_sql}",
            tuple(values[name] for name in selected),
        )
        seeded += 1
    if commit:
        db.conn.commit()
    return seeded


def get_inventory_runes(inventory_id):
    db = _db()
    rows = db.conn.execute(
        """
        SELECT id, inventory_id, slot_index, rune_item_id,
               rune_stat, rune_level, inserted_at
        FROM inventory_runes
        WHERE inventory_id=?
        ORDER BY slot_index, id
        """,
        (int(inventory_id),),
    ).fetchall()
    return [
        {
            "id": row[0], "inventory_id": row[1], "slot_index": row[2],
            "rune_item_id": row[3], "stat": row[4], "level": row[5],
            "bonus": row[5], "inserted_at": row[6],
        }
        for row in rows
    ]


def get_inventory_rune_capacity(inventory_id):
    db = _db()
    row = db.conn.execute(
        """
        SELECT items.slot_key
        FROM inventory JOIN items ON items.id=inventory.item_id
        WHERE inventory.id=?
        """,
        (int(inventory_id),),
    ).fetchone()
    return get_rune_slot_limit(row[0] if row else "")


def get_inventory_rune_socket_summary(inventory_id):
    runes = get_inventory_runes(inventory_id)
    capacity = get_inventory_rune_capacity(inventory_id)
    return {
        "inventory_id": int(inventory_id),
        "used": len(runes),
        "capacity": capacity,
        "free": max(0, capacity - len(runes)),
        "runes": runes,
    }


def get_equipped_rune_stat_totals(user_id):
    """Read API prepared for 10.7.0. No stat integration is active yet."""
    db = _db()
    totals = {"str": 0, "sta": 0, "dex": 0, "int": 0, "wis": 0}
    rows = db.conn.execute(
        """
        SELECT ir.rune_stat, ir.rune_level
        FROM equipment_slots es
        JOIN inventory i ON i.id=es.inventory_id AND i.user_id=es.user_id
        JOIN inventory_runes ir ON ir.inventory_id=i.id
        WHERE es.user_id=? AND COALESCE(i.durability, 100) > 0
        """,
        (int(user_id),),
    ).fetchall()
    for stat, level in rows:
        key = str(stat).lower()
        if key in totals:
            totals[key] += int(level or 0)
    return totals


def validate_rune_fusion_selection(rune_item_ids):
    """Validate the future 3-rune recipe and return a user-facing reason."""
    try:
        selected = [int(item_id) for item_id in rune_item_ids]
    except Exception:
        selected = []
    if len(selected) != RUNE_FUSION_SOURCE_QUANTITY:
        return {
            "success": False,
            "code": "wrong_quantity",
            "message": "❌ Для переробки потрібно вибрати рівно 3 однакові руни.",
        }
    definitions = [get_rune_definition(item_id) for item_id in selected]
    if any(definition is None for definition in definitions):
        return {
            "success": False,
            "code": "not_rune",
            "message": "❌ Для переробки можна використовувати лише руни характеристик.",
        }
    keys = {(definition["stat"], definition["level"]) for definition in definitions}
    if len(keys) != 1:
        return {
            "success": False,
            "code": "different_runes",
            "message": "❌ Потрібно вибрати 3 однакові руни одного типу й рівня.",
        }
    definition = definitions[0]
    if definition["level"] >= 5:
        return {
            "success": False,
            "code": "max_level",
            "message": "❌ Руна V вже має максимальний рівень і не переробляється.",
        }
    result_item_id = get_rune_item_id(definition["stat"], definition["level"] + 1)
    return {
        "success": True,
        "code": "ok",
        "message": "✅ Руни підходять для переробки.",
        "source_item_id": definition["id"],
        "result_item_id": result_item_id,
        "source_quantity": RUNE_FUSION_SOURCE_QUANTITY,
        "token_item_id": FIRIUS_TOKEN_ITEM_ID,
        "token_quantity": RUNE_FUSION_TOKEN_QUANTITY,
    }
'''

DB_FACADE = r'''

# ==============================
# ROM 10.2.0 RUNE SYSTEM DATA MODEL FACADE
# ==============================

def init_rune_system():
    from systems.rune_system import init_rune_system as _func
    return _func()


def seed_rune_system_items(commit=True):
    from systems.rune_system import seed_rune_system_items as _func
    return _func(commit=commit)


def get_inventory_runes(inventory_id):
    from systems.rune_system import get_inventory_runes as _func
    return _func(inventory_id)


def get_inventory_rune_capacity(inventory_id):
    from systems.rune_system import get_inventory_rune_capacity as _func
    return _func(inventory_id)


def get_inventory_rune_socket_summary(inventory_id):
    from systems.rune_system import get_inventory_rune_socket_summary as _func
    return _func(inventory_id)


def get_equipped_rune_stat_totals(user_id):
    from systems.rune_system import get_equipped_rune_stat_totals as _func
    return _func(user_id)


def validate_rune_fusion_selection(rune_item_ids):
    from systems.rune_system import validate_rune_fusion_selection as _func
    return _func(rune_item_ids)
'''

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import importlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    import db
    from data import runes
    from systems import rune_system

    result = db.init_rune_system()
    if result.get("success") is not True or result.get("seeded") != 28:
        fail(f"init contract failed: {result}")

    columns = {row[1] for row in db.conn.execute("PRAGMA table_info(inventory_runes)")}
    required = {"id", "inventory_id", "slot_index", "rune_item_id", "rune_stat", "rune_level", "inserted_at"}
    if not required.issubset(columns):
        fail(f"inventory_runes columns missing: {required - columns}")

    rows = db.conn.execute(
        "SELECT id, type, category, max_stack, sell_price FROM items "
        "WHERE id BETWEEN 501 AND 528 ORDER BY id"
    ).fetchall()
    if len(rows) != 28:
        fail(f"rune-system seed rows={len(rows)}, expected 28")
    if len({row[1] for row in rows}) != 28:
        fail("rune-system item types are not unique")
    if any(int(row[3] or 0) != 999 for row in rows):
        fail("rune-system max_stack contract failed")
    if any(float(row[4] or 0) != 0.0 for row in rows):
        fail("rune-system items must not be sellable")

    if len(runes.RUNE_ITEM_DEFINITIONS) != 25:
        fail("expected 25 canonical rune definitions")
    if sum(runes.RUNE_SLOT_LIMITS.values()) != 14:
        fail("expected 14 total equipment rune slots")
    if runes.FIRIUS_TOKENS_PER_DAILY_REWARD != 10:
        fail("daily Firius token reward must be 10")

    same = db.validate_rune_fusion_selection([501, 501, 501])
    mixed_type = db.validate_rune_fusion_selection([501, 506, 501])
    mixed_level = db.validate_rune_fusion_selection([501, 502, 501])
    wrong_count = db.validate_rune_fusion_selection([501, 501])
    max_level = db.validate_rune_fusion_selection([505, 505, 505])
    if not same.get("success") or same.get("result_item_id") != 502:
        fail(f"same-rune fusion selection failed: {same}")
    for result in (mixed_type, mixed_level):
        if result.get("code") != "different_runes" or "3 однакові руни" not in result.get("message", ""):
            fail(f"mixed rune validation message failed: {result}")
    if wrong_count.get("code") != "wrong_quantity":
        fail(f"wrong quantity contract failed: {wrong_count}")
    if max_level.get("code") != "max_level":
        fail(f"max-level contract failed: {max_level}")

    if db.get_equipped_rune_stat_totals(-999999999) != {"str": 0, "sta": 0, "dex": 0, "int": 0, "wis": 0}:
        fail("missing-user rune totals contract failed")

    quick = db.conn.execute("PRAGMA quick_check").fetchone()[0]
    if quick != "ok":
        fail(f"quick_check={quick}")

    print("[OK] Rune/Firius data model contracts")
    print("- canonical rune definitions: 25")
    print("- utility item definitions: 3")
    print("- seeded item rows 501-528: 28")
    print("- normalized inventory_runes schema: OK")
    print("- equipment rune slots total: 14")
    print("- Firius Tokens per daily reward: 10")
    print("- mixed rune type/level validation: OK")
    print("- user message: Потрібно вибрати 3 однакові руни одного типу й рівня.")
    print("- Rune V fusion rejection: OK")
    print("- stat integration active: no (reserved for 10.7.0)")
    print("- database quick_check: ok")


if __name__ == "__main__":
    main()
'''


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (root / DB_REL).is_file() and (root / MAIN_REL).is_file() and (root / "game.db").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def add_db_facade(source):
    if "ROM 10.2.0 RUNE SYSTEM DATA MODEL FACADE" in source:
        return source
    return source.rstrip() + DB_FACADE + "\n"


def add_main_integration(source):
    if "from db import init_rune_system" not in source:
        anchor = "from db import run_db_startup_maintenance\n"
        if anchor not in source:
            raise RuntimeError("main.py startup import anchor not found")
        source = source.replace(anchor, anchor + "from db import init_rune_system\n", 1)
    if "_rune_system_init_result = init_rune_system()" not in source:
        anchor = "seed_items()\n"
        if anchor not in source:
            raise RuntimeError("main.py seed_items anchor not found")
        block = (
            "_rune_system_init_result = init_rune_system()\n"
            "if _rune_system_init_result.get(\"success\"):\n"
            "    print(f\"✅ RUNE SYSTEM DATA MODEL: {_rune_system_init_result}\")\n\n"
        )
        source = source.replace(anchor, block + anchor, 1)
    ast.parse(source, filename="main.py")
    return source


def run(root, path, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{path.name} exit code {result.returncode}")


def main():
    root = find_root()
    paths = {
        DATA_REL: DATA_SOURCE,
        SYSTEM_REL: SYSTEM_SOURCE,
        MIGRATION_REL: MIGRATION_SOURCE,
        TEST_REL: TEST_SOURCE,
    }
    db_path = root / DB_REL
    main_path = root / MAIN_REL
    original_db = db_path.read_text(encoding="utf-8-sig")
    original_main = main_path.read_text(encoding="utf-8-sig")
    updated_db = add_db_facade(original_db)
    updated_main = add_main_integration(original_main)

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = {}
    touched = [DB_REL, MAIN_REL, DATA_REL, SYSTEM_REL, MIGRATION_REL, TEST_REL]
    for rel in touched:
        path = root / rel
        if path.exists():
            backup = backup_dir / f"{str(rel).replace('/', '_').replace(chr(92), '_')}_{PATCH_ID}_{stamp}.bak"
            shutil.copy2(path, backup)
            backups[rel] = backup
    database_backup = backup_dir / f"game.db_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(root / "game.db", database_backup)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        for rel, content in paths.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        db_path.write_text(updated_db, encoding="utf-8")
        main_path.write_text(updated_main, encoding="utf-8")

        for rel in touched:
            py_compile.compile(str(root / rel), doraise=True)

        # Apply the versioned migration, then initialize/seed through public API.
        run(root, root / "tools" / "migration_status.py", env)
        code = (
            "import db; "
            "result=db.run_pending_migrations(); "
            "print('[OK] migrations', result); "
            "init=db.init_rune_system(); "
            "print('[OK] rune init', init)"
        )
        result = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"migration/rune init exit code {result.returncode}")

        checks = [
            TEST_REL,
            Path("tools/smoke_test_inventory_refine_contracts.py"),
            Path("tools/smoke_test_equipment_readonly_core.py"),
            Path("tools/smoke_test_player_combat_stats.py"),
            Path("tools/smoke_test_rom_core.py"),
            Path("tools/check_imports.py"),
        ]
        for rel in checks:
            if not (root / rel).is_file():
                raise RuntimeError(f"missing check: {rel}")
            run(root, root / rel, env)

        conn = sqlite3.connect(root / "game.db")
        try:
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
            count = conn.execute("SELECT COUNT(*) FROM items WHERE id BETWEEN 501 AND 528").fetchone()[0]
            table = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='inventory_runes'"
            ).fetchone()[0]
        finally:
            conn.close()
        if quick != "ok" or count != 28 or table != 1:
            raise RuntimeError(f"final DB contract failed: quick={quick}, items={count}, table={table}")

    except Exception as exc:
        shutil.copy2(database_backup, root / "game.db")
        for rel in touched:
            path = root / rel
            if rel in backups:
                shutil.copy2(backups[rel], path)
            elif path.exists():
                path.unlink()
        fail(f"Перевірка не пройдена; код і game.db відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Створено data/runes.py та systems/rune_system.py.")
    print("✅ Створено таблицю inventory_runes та два індекси.")
    print("✅ Додано 25 рун, Жетон Фіріуса і два екстрактори (ID 501-528).")
    print("✅ Додано перевірку майбутньої переробки: тільки 3 однакові руни одного типу й рівня.")
    print("✅ Руни ще не впливають на характеристики й не доступні через UI.")
    print("Резервні копії:")
    print(f"   {database_backup.relative_to(root)}")
    for rel, backup in backups.items():
        print(f"   {backup.relative_to(root)}")
    print("Перевірки:")
    print("   python ./tools/smoke_test_rune_data_model.py")
    print("   python ./tools/smoke_test_inventory_refine_contracts.py")
    print("   python ./tools/smoke_test_equipment_readonly_core.py")
    print("   python ./tools/smoke_test_player_combat_stats.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")


if __name__ == "__main__":
    main()
