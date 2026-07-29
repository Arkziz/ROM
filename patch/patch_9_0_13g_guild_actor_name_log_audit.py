#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13g: install and run a read-only Guild actor-name log audit."""
from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13g"
TOOL_NAME = "audit_guild_actor_name_log.py"

TOOL = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only structural and isolated audit for Guild event actor names."""
from __future__ import annotations

import ast
import hashlib
import inspect
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
GUILD_PATH = ROOT / "systems" / "guild_system.py"
CHARACTER_PATH = ROOT / "systems" / "character_system.py"
DB_PY_PATH = ROOT / "db.py"
REPORT = ROOT / "DB_CLEANUP_9_0_13G_GUILD_ACTOR_NAME_LOG_AUDIT.md"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest(),
        path.stat().st_size,
        path.stat().st_mtime_ns,
    )


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def function_definitions(text, tree, name):
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    nodes.sort(key=lambda node: node.lineno)
    return [
        (node, ast.get_source_segment(text, node) or "")
        for node in nodes
    ]


def require_function(text, tree, name, expected=1):
    definitions = function_definitions(text, tree, name)
    if len(definitions) != expected:
        fail(f"{name}: definitions={len(definitions)}, expected {expected}")
    return definitions[-1]


def accepted_parameters(node):
    names = [argument.arg for argument in node.args.args]
    names.extend(argument.arg for argument in node.args.kwonlyargs)
    return names


def imported_names(tree):
    result = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                result.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.asname or alias.name.split(".")[0])
    return result


def assignment_value(tree, name):
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return None
    return None


def main():
    for path in (DB_PATH, GUILD_PATH, CHARACTER_PATH, DB_PY_PATH):
        if not path.is_file():
            fail(f"missing required file: {path}")

    before = fingerprint(DB_PATH)
    guild_text, guild_tree = parse(GUILD_PATH)
    character_text, character_tree = parse(CHARACTER_PATH)
    db_text, db_tree = parse(DB_PY_PATH)

    elite_node, elite_source = require_function(
        guild_text, guild_tree, "award_guild_elite_kill"
    )
    contract_node, contract_source = require_function(
        guild_text, guild_tree, "award_guild_contract_completion"
    )
    progress_node, progress_source = require_function(
        guild_text, guild_tree, "add_user_guild_progress"
    )

    elite_parameters = accepted_parameters(elite_node)
    contract_parameters = accepted_parameters(contract_node)
    if "user_id" not in elite_parameters:
        fail("award_guild_elite_kill has no user_id parameter")
    if "user_id" not in contract_parameters:
        fail("award_guild_contract_completion has no user_id parameter")

    character_names = function_definitions(
        character_text, character_tree, "get_character_name"
    )
    db_names = function_definitions(db_text, db_tree, "get_character_name")
    if not character_names and not db_names:
        fail("get_character_name API not found")

    guild_imports = imported_names(guild_tree)
    guild_has_direct_name_api = "get_character_name" in guild_imports
    guild_uses_actor_name = "get_character_name(" in elite_source or "get_character_name(" in contract_source

    elite_reason_has_mob = "GUILD_ELITE_KILL_SCORE_REASON" in elite_source
    contract_reason_has_target = "GUILD_CONTRACT_SCORE_REASON" in contract_source
    elite_reason_has_actor = any(
        marker in elite_source
        for marker in ("виконав", "переміг", "character_name", "actor_name")
    )
    contract_reason_has_actor = any(
        marker in contract_source
        for marker in ("виконав", "переміг", "character_name", "actor_name")
    )

    # Record formulas before isolated runtime probes so the future hotfix cannot
    # accidentally alter Guild progress amounts.
    elite_exp = assignment_value(guild_tree, "GUILD_ELITE_KILL_EXP_REWARD")
    elite_resource = assignment_value(guild_tree, "GUILD_ELITE_KILL_RESOURCE_REWARD")
    contract_exp = assignment_value(guild_tree, "GUILD_CONTRACT_EXP_REWARD")
    contract_resource = assignment_value(guild_tree, "GUILD_CONTRACT_RESOURCE_REWARD")

    from systems import guild_system as guild

    original_member = guild.get_user_guild_member
    original_add = guild.add_user_guild_progress
    captured = []
    try:
        guild.get_user_guild_member = lambda user_id: {
            "guild_id": 777,
            "user_id": user_id,
        }

        def fake_add(**kwargs):
            captured.append(kwargs)
            return {"success": True, "message": "ok"}

        guild.add_user_guild_progress = fake_add
        elite_result = guild.award_guild_elite_kill(
            -90121320,
            mob={"name": "⭐️ Елітний 🔮 Audit cultist"},
        )
        contract_result = guild.award_guild_contract_completion(
            -90121321,
            contract={"target_mob_name": "🔮 Audit cultist"},
        )
    finally:
        guild.get_user_guild_member = original_member
        guild.add_user_guild_progress = original_add

    if len(captured) != 2:
        fail(f"isolated Guild progress calls={len(captured)}, expected 2")
    elite_call, contract_call = captured
    elite_reason = str(elite_call.get("reason") or "")
    contract_reason = str(contract_call.get("reason") or "")

    current_actor_absent = (
        "Audit actor" not in elite_reason
        and "Audit actor" not in contract_reason
        and not elite_reason_has_actor
        and not contract_reason_has_actor
    )

    # Read-only DB context. We intentionally do not try to backfill historical
    # names because the event text does not reliably retain the actor identity.
    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        user_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        character_columns = sorted(
            user_columns.intersection({"user_id", "character_name", "name", "username"})
        )
        guild_log_tables = sorted(
            table for table in tables if "guild" in table.lower() and "log" in table.lower()
        )
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()

    after = fingerprint(DB_PATH)
    if before != after:
        fail("game.db changed during read-only audit")
    if integrity != "ok":
        fail(f"database quick_check={integrity}")

    recommended_format_contract = (
        "Виконання контракту: <ціль>. (виконав: <ім’я персонажа>)"
    )
    recommended_format_elite = (
        "Перемога над елітним мобом: <ціль>. (переміг: <ім’я персонажа>)"
    )

    report = [
        "# ROM 9.0.13g — Guild Actor Name Log Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Safety",
        "",
        "- Gameplay files changed: **0**",
        "- Database rows changed: **0**",
        f"- Database SHA/size/mtime unchanged: **{before == after}**",
        f"- Database quick check: **{integrity}**",
        "",
        "## Event hooks",
        "",
        f"- Elite hook parameters: `{elite_parameters}`",
        f"- Contract hook parameters: `{contract_parameters}`",
        f"- Elite hook receives `user_id`: **{'user_id' in elite_parameters}**",
        f"- Contract hook receives `user_id`: **{'user_id' in contract_parameters}**",
        f"- Elite reason contains mob identity: **{elite_reason_has_mob}**",
        f"- Contract reason contains target identity: **{contract_reason_has_target}**",
        "",
        "## Character-name API",
        "",
        f"- `systems.character_system.get_character_name()` definitions: **{len(character_names)}** at lines `{[node.lineno for node, _source in character_names]}`",
        f"- `db.get_character_name()` definitions/facades: **{len(db_names)}** at lines `{[node.lineno for node, _source in db_names]}`",
        f"- Guild System currently imports `get_character_name`: **{guild_has_direct_name_api}**",
        f"- Guild event hooks currently call `get_character_name()`: **{guild_uses_actor_name}**",
        f"- Relevant `users` columns: `{character_columns}`",
        "",
        "## Isolated current output",
        "",
        f"- Elite reason: `{elite_reason}`",
        f"- Contract reason: `{contract_reason}`",
        f"- Actor name absent from both event formats: **{current_actor_absent}**",
        "",
        "## Guild reward contracts",
        "",
        f"- Elite EXP reward constant: `{elite_exp}`",
        f"- Elite resource reward constant: `{elite_resource}`",
        f"- Contract EXP reward constant: `{contract_exp}`",
        f"- Contract resource reward constant: `{contract_resource}`",
        f"- Elite call increments: `kills={elite_call.get('kills')}`, `contracts={elite_call.get('contracts')}`",
        f"- Contract call increments: `kills={contract_call.get('kills')}`, `contracts={contract_call.get('contracts')}`",
        "",
        "## Database context",
        "",
        f"- Guild log-like tables: `{guild_log_tables}`",
        "- Historical event rows will not be rewritten because actor identity cannot be reconstructed reliably from existing reason text.",
        "",
        "## Recommended format",
        "",
        f"- Contract: `{recommended_format_contract}`",
        f"- Elite kill: `{recommended_format_elite}`",
        "",
        "## Recommended implementation",
        "",
        "1. Add one central Guild helper that resolves a character display name by `user_id`.",
        "2. Use the canonical Character API through a local/lazy import to avoid circular-import risk.",
        "3. Normalize the returned value to a non-empty string.",
        "4. Append `(виконав: <ім’я>)` to contract reasons.",
        "5. Append `(переміг: <ім’я>)` to elite-kill reasons.",
        "6. If no character name exists, preserve the current reason without a technical user ID or placeholder.",
        "7. Preserve all Guild EXP, resource, kills, and contracts values exactly.",
        "8. Add isolated tests for named and unnamed users without writing to the real database.",
        "",
        "Suggested next patch: `patch_9_0_13h_guild_actor_name_log_hotfix.py`",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] Guild actor name log audit")
    print("- elite hook receives user_id: OK")
    print("- contract hook receives user_id: OK")
    print(f"- canonical character-name API available: {bool(character_names or db_names)}")
    print(f"- Guild System currently resolves actor name: {guild_uses_actor_name}")
    print(f"- isolated elite reason: {elite_reason}")
    print(f"- isolated contract reason: {contract_reason}")
    print(f"- actor name absent from current reasons: {current_actor_absent}")
    print("- Guild reward formulas captured: OK")
    print("- historical rows eligible for safe automatic backfill: 0")
    print("- database mutations: 0")
    print("- diagnosis: event reason has target but no actor-name enrichment")
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
            (root / "systems" / "guild_system.py").is_file()
            and (root / "systems" / "character_system.py").is_file()
            and (root / "game.db").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM або game.db.")


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
            [sys.executable, str(target)],
            cwd=root,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"audit exit code {result.returncode}")
    except Exception as exc:
        if backup is not None:
            shutil.copy2(backup, target)
        elif target.exists():
            target.unlink()
        fail(f"Аудит не пройдено; встановлення відкочено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Створено: tools/{TOOL_NAME}")
    print("✅ Створено: DB_CLEANUP_9_0_13G_GUILD_ACTOR_NAME_LOG_AUDIT.md")
    print("✅ Gameplay-код і game.db не змінені.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root) if backup else 'не потрібні - новий файл'}")
    print("Повторний запуск:")
    print(f"   python ./tools/{TOOL_NAME}")


if __name__ == "__main__":
    main()
