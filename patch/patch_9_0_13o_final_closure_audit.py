#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13o: install and run the final read-only closure audit."""
from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13o"
TOOL_NAME = "audit_9_0_13_final_closure.py"

TOOL = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final read-only closure audit for the ROM 9.0.13 cleanup cycle."""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
MAIN_PY = ROOT / "main.py"
REPORT = ROOT / "DB_CLEANUP_9_0_13O_FINAL_CLOSURE_AUDIT.md"

REMOVED_CAPTURES = (
    "_base_get_inventory_detailed_before_refine_display_v1",
    "_base_get_inventory_entry_before_refine_display_v1",
    "_base_get_item_by_inventory_id_before_refine_display_v1",
    "_base_get_item_by_inventory_id_full_before_refine_display_v1",
    "_base_get_max_hp_before_refine_v1",
    "_base_get_sellable_equipment_items_before_refine_display_v1",
    "_base_get_weapon_damage_by_inventory_id_before_refine_v1",
    "_base_get_weapon_damage_for_refine_hotfix_v1",
)

CANONICAL_GROUPS = {
    "data.classes": (
        "CLASS_CONFIGS", "CLASS_RESET_SPHERE_ITEM_ID",
    ),
    "data.equipment_profiles": (
        "ARMOR_ALLOWED_BY_CLASS", "ARMOR_EXTRA_STATS_BY_SLOT",
        "ARMOR_TYPE_LABELS", "EQUIPMENT_SLOTS", "ITEM_SUBTYPE_LABELS",
        "MAIN_HAND_ALLOWED_BY_CLASS", "MAIN_HAND_PROFILES",
        "OFF_HAND_ALLOWED_BY_CLASS", "OFF_HAND_PROFILES",
    ),
    "data.balance": (
        "CONTRACTS_UNLOCK_LEVEL", "CONTRACT_MOBS_EQUIVALENT",
        "CONTRACT_TARGET_KILLS", "DAILY_CONTRACT_LIMIT",
        "DAILY_QUEST_ID_KILL_MONSTERS", "DAILY_QUEST_REWARD_ITEM_ID",
        "DAILY_QUEST_REWARD_QUANTITY", "DAILY_QUEST_TARGET_KILLS",
        "ENERGY_MAX", "ENERGY_REGEN_MINUTES", "HP_REGEN_MINUTES",
        "HP_REGEN_PERCENT", "RARITY_REPAIR_MULTIPLIERS",
        "REFINE_MATERIAL_MAX_STACK", "REFINE_STONE_ITEM_ID",
    ),
}
ALL_CONSTANTS = tuple(name for names in CANONICAL_GROUPS.values() for name in names)

REQUIRED_TESTS = (
    "smoke_test_static_item_seed_contracts.py",
    "smoke_test_explicit_db_startup_maintenance.py",
    "smoke_test_capture_only_cleanup.py",
    "smoke_test_constants_canonicalization.py",
    "smoke_test_class_change_handler_contract.py",
    "smoke_test_guild_contract_target_log.py",
    "smoke_test_guild_actor_name_log.py",
    "smoke_test_combat_mana_potion_contracts.py",
    "smoke_test_combat_potion_cooldown_menu_ux.py",
    "smoke_test_character_mutation_contracts.py",
    "smoke_test_contract_contracts.py",
    "smoke_test_inventory_refine_contracts.py",
    "smoke_test_equipment_readonly_core.py",
    "smoke_test_equipment_trader_contracts.py",
    "smoke_test_auction_lifecycle_contracts.py",
    "smoke_test_player_combat_stats.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
    }


def logical_database_snapshot(path):
    """Hash logical table contents, ignoring SQLite file-level metadata churn."""
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        tables = [
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        snapshot = {}
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            columns = [
                row[1] for row in conn.execute(f"PRAGMA table_info({quoted})").fetchall()
            ]
            order = ", ".join(
                '"' + column.replace('"', '""') + '"' for column in columns
            ) or "rowid"
            rows = conn.execute(f"SELECT * FROM {quoted} ORDER BY {order}").fetchall()
            normalized = [
                [value.hex() if isinstance(value, bytes) else value for value in row]
                for row in rows
            ]
            payload = json.dumps(
                normalized, ensure_ascii=False, sort_keys=True, default=str
            ).encode("utf-8")
            snapshot[table] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        return snapshot
    finally:
        conn.close()


def logical_snapshot_diff(before, after):
    return [
        table for table in sorted(set(before) | set(after))
        if before.get(table) != after.get(table)
    ]


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def assigned_names(node):
    names = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            names.add(target.id)
    return names


def run_checked(path, env):
    result = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT, env=env,
        text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )
    return {
        "name": path.name,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def sandbox_import_fingerprint():
    with tempfile.TemporaryDirectory(prefix="rom_9_0_13o_") as temp_name:
        temp = Path(temp_name)
        sandbox_db = temp / "game.db"
        shutil.copy2(DB_PATH, sandbox_db)
        before = fingerprint(sandbox_db)
        probe = temp / "probe.py"
        probe.write_text(
            "import sys\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            "import db\n"
            "print('[OK] final sandbox import db')\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(probe)], cwd=temp, env=env,
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False,
        )
        after = fingerprint(sandbox_db)
        return result, before == after


def main():
    for path in (DB_PATH, DB_PY, MAIN_PY):
        if not path.is_file():
            fail(f"missing required file: {path}")
    for name in REQUIRED_TESTS:
        if not (ROOT / "tools" / name).is_file():
            fail(f"missing required closure test: tools/{name}")

    real_before = fingerprint(DB_PATH)
    logical_before = logical_database_snapshot(DB_PATH)
    db_text, db_tree = parse(DB_PY)
    main_text, main_tree = parse(MAIN_PY)

    # Static item contracts and physical rows.
    import db
    seed_source = ast.get_source_segment(
        db_text,
        next(node for node in db_tree.body if isinstance(node, ast.FunctionDef) and node.name == "seed_items"),
    ) or ""
    seed_ids = set()
    for node in ast.walk(ast.parse(seed_source)):
        if isinstance(node, ast.Tuple):
            try:
                value = ast.literal_eval(node)
            except Exception:
                continue
            if isinstance(value, tuple) and len(value) >= 5 and isinstance(value[0], int):
                seed_ids.add(value[0])
    if seed_ids != {201, 202, 203, 204}:
        fail(f"seed_items IDs={sorted(seed_ids)}, expected [201, 202, 203, 204]")

    conn = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        legacy_rows = int(conn.execute(
            "SELECT COUNT(*) FROM items WHERE id BETWEEN 1 AND 26"
        ).fetchone()[0] or 0)
        sphere = conn.execute("SELECT name, type FROM items WHERE id=301").fetchone()
        quick_check = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()
    if legacy_rows != 0:
        fail(f"legacy equipment rows 1-26 remain: {legacy_rows}")
    if not sphere or sphere[1] != "class_reset" or "Сфера нового шляху" not in sphere[0]:
        fail(f"item 301 is not the canonical class-reset sphere: {sphere}")
    if quick_check != "ok":
        fail(f"database quick_check={quick_check}")

    # No hidden maintenance calls.
    target_calls = {
        "ensure_refine_material_stack_sizes",
        "migrate_active_contracts_target_kills_to_5",
    }
    hidden_calls = []
    for statement in db_tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and call_name(node) in target_calls:
                hidden_calls.append((call_name(node), node.lineno))
    if hidden_calls:
        fail(f"hidden DB startup calls remain: {hidden_calls}")
    startup_calls = [
        node for node in ast.walk(main_tree)
        if isinstance(node, ast.Call) and call_name(node) == "run_db_startup_maintenance"
    ]
    if len(startup_calls) != 1:
        fail(f"explicit DB startup maintenance calls={len(startup_calls)}, expected 1")

    # Removed captures stay removed.
    residual_captures = []
    for node in ast.walk(db_tree):
        if isinstance(node, ast.Name) and node.id in REMOVED_CAPTURES:
            residual_captures.append((node.id, node.lineno))
        elif isinstance(node, ast.Constant) and node.value in REMOVED_CAPTURES:
            residual_captures.append((node.value, node.lineno))
    if residual_captures:
        fail(f"obsolete captures remain: {residual_captures}")

    # Constants are canonical imports with no local definitions.
    local_constants = []
    imported = {}
    for node in db_tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            local_constants.extend(
                (name, node.lineno) for name in assigned_names(node).intersection(ALL_CONSTANTS)
            )
        elif isinstance(node, ast.ImportFrom) and node.module in CANONICAL_GROUPS:
            for alias in node.names:
                imported[alias.asname or alias.name] = node.module
    if local_constants:
        fail(f"local canonical constants remain: {local_constants}")
    for module_name, names in CANONICAL_GROUPS.items():
        canonical = importlib.import_module(module_name)
        for name in names:
            if imported.get(name) != module_name:
                fail(f"wrong canonical import owner for {name}: {imported.get(name)}")
            if getattr(db, name) != getattr(canonical, name):
                fail(f"canonical constant value mismatch: {name}")

    # Feature markers fixed during 9.0.13.
    contracts_text = (ROOT / "systems" / "contract_system.py").read_text(encoding="utf-8-sig")
    guild_text = (ROOT / "systems" / "guild_system.py").read_text(encoding="utf-8-sig")
    potion_text = (ROOT / "systems" / "potion_system.py").read_text(encoding="utf-8-sig")
    combat_text = (ROOT / "handlers" / "combat.py").read_text(encoding="utf-8-sig")
    start_text = (ROOT / "handlers" / "start.py").read_text(encoding="utf-8-sig")
    markers = {
        "contract target snapshot": 'contract=contract' in contracts_text,
        "guild target name": 'contract.get("target_mob_name")' in guild_text,
        "guild actor contract": "(виконав: {actor_name})" in guild_text,
        "guild actor elite": "(переміг: {actor_name})" in guild_text,
        "MP potion result": '"resource": "mp"' in potion_text,
        "MP combat menu": 'is_mp_potion = type_ in ("potion_mp", "potion_mp_medium")' in combat_text,
        "cooldown menu UX": "доступно через {format_combat_turns_uk(cooldown)}" in combat_text,
        "class-change bool contract": "consume_success = bool(consume_result)" in start_text,
    }
    missing_markers = [name for name, ok in markers.items() if not ok]
    if missing_markers:
        fail(f"9.0.13 feature markers missing: {missing_markers}")

    sandbox_result, import_unchanged = sandbox_import_fingerprint()
    if sandbox_result.returncode != 0:
        fail(f"sandbox import db failed: {sandbox_result.stderr or sandbox_result.stdout}")
    if not import_unchanged:
        fail("plain import db changed sandbox game.db")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    results = []
    for name in REQUIRED_TESTS:
        result = run_checked(ROOT / "tools" / name, env)
        results.append(result)
        print(result["stdout"], end="")
        if result["stderr"]:
            print(result["stderr"], end="", file=sys.stderr)
        if result["returncode"] != 0:
            fail(f"closure test failed: {name} exit code {result['returncode']}")

    readiness = run_checked(ROOT / "tools" / "db_cleanup_readiness.py", env)
    print(readiness["stdout"], end="")
    if readiness["returncode"] != 0:
        fail(f"db_cleanup_readiness exit code {readiness['returncode']}")
    readiness_markers = (
        "duplicates: 0", "legacy_refs: 0",
        "unsafe_delete: 0", "maybe_cleanup_later: 0",
    )
    for marker in readiness_markers:
        if marker not in readiness["stdout"]:
            fail(f"readiness missing {marker}")

    real_after = fingerprint(DB_PATH)
    logical_after = logical_database_snapshot(DB_PATH)
    changed_tables = logical_snapshot_diff(logical_before, logical_after)
    if changed_tables:
        fail(
            "logical real game.db contents changed during final closure audit: "
            f"{changed_tables}. Stop the bot and rerun the audit."
        )
    file_fingerprint_changed = real_before != real_after

    report = [
        "# ROM 9.0.13o — Final Closure Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Final status",
        "",
        "**ROM 9.0.13 cleanup status: COMPLETE**",
        "",
        "## Safety",
        "",
        f"- Real database logical contents unchanged: **{not changed_tables}**",
        f"- SQLite file fingerprint unchanged: **{not file_fingerprint_changed}**",
        "- File fingerprint changes alone are treated as SQLite metadata/WAL activity, not gameplay mutation.",
        f"- Database quick check: **{quick_check}**",
        f"- Plain `import db` changes sandbox DB: **{not import_unchanged}**",
        "- Gameplay files changed by this audit: **0**",
        "- Real database rows changed by this audit: **0**",
        "",
        "## Closed workstreams",
        "",
        "- Static seed cleanup: **PASS**",
        "- Legacy equipment rows 1-26 removed: **PASS**",
        "- Canonical item 301 class-reset sphere: **PASS**",
        "- Explicit DB startup maintenance: **PASS**",
        "- Obsolete `_base_*` captures removed: **PASS**",
        "- 26 constants canonicalized to `data/*`: **PASS**",
        "- Class-reset sphere callback contract: **PASS**",
        "- Guild contract target logging: **PASS**",
        "- Guild actor-name logging: **PASS**",
        "- Combat MP potions and cooldown UX: **PASS**",
        "- Auction lifecycle contracts: **PASS**",
        "- Compile and safe imports: **PASS**",
        "- DB cleanup readiness: **PASS**",
        "",
        "## Feature markers",
        "",
    ]
    for name, ok in markers.items():
        report.append(f"- {name}: **{'PASS' if ok else 'FAIL'}**")
    report.extend([
        "",
        "## Automated test suite",
        "",
    ])
    for result in results:
        report.append(f"- `{result['name']}`: **PASS**")
    report.extend([
        "- `db_cleanup_readiness.py`: **PASS**",
        "",
        "## Readiness",
        "",
        "```text",
        readiness["stdout"].strip(),
        "```",
        "",
        "## Closure decision",
        "",
        "All planned ROM 9.0.13 cleanup, compatibility, startup, constants, Guild logging, and combat-potion workstreams have passed their structural and runtime contracts. No additional 9.0.13 cleanup patch is required unless manual gameplay verification reveals a new defect.",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] ROM 9.0.13 final closure audit")
    print("- status: COMPLETE")
    print(f"- closure tests passed: {len(results)}")
    print("- static item cleanup: PASS")
    print("- explicit DB startup maintenance: PASS")
    print("- compatibility captures cleanup: PASS")
    print("- constants canonicalization: PASS")
    print("- Guild logging fixes: PASS")
    print("- combat MP potion implementation: PASS")
    print("- readiness: PASS")
    print("- gameplay mutations: 0")
    print("- real database logical mutations: 0")
    print(f"- SQLite file fingerprint changed: {file_fingerprint_changed}")
    print(f"- report: {REPORT}")


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
        if (
            (root / "db.py").is_file()
            and (root / "main.py").is_file()
            and (root / "game.db").is_file()
            and (root / "tools" / "check_imports.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def main():
    root = find_root()
    target = root / "tools" / TOOL_NAME
    backup = None

    if target.exists() and target.read_text(encoding="utf-8-sig") != TOOL:
        backup_dir = root / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backup_dir / f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(target, backup)

    target.write_text(TOOL, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        py_compile.compile(str(target), doraise=True)
        result = subprocess.run(
            [sys.executable, str(target)], cwd=root, env=env, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"audit exit code {result.returncode}")
    except Exception as exc:
        if backup is not None:
            shutil.copy2(backup, target)
        elif target.exists():
            target.unlink()
        fail(f"Фінальний аудит не пройдено; встановлення audit tool відкочено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Створено: tools/{TOOL_NAME}")
    print("✅ Створено: DB_CLEANUP_9_0_13O_FINAL_CLOSURE_AUDIT.md")
    print("✅ Gameplay-код і реальна game.db не змінені.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root) if backup else 'не потрібні - новий файл'}")
    print("Повторний запуск:")
    print(f"   python ./tools/{TOOL_NAME}")


if __name__ == "__main__":
    main()
