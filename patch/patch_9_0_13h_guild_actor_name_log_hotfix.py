#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13h: add character names to Guild contract and elite-kill logs."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13h"
TARGET_REL = Path("systems") / "guild_system.py"
TEST_NAME = "smoke_test_guild_actor_name_log.py"
TESTS = (
    TEST_NAME,
    "smoke_test_guild_contract_target_log.py",
    "smoke_test_contract_reward_direct_facade.py",
    "smoke_test_auction_lifecycle_contracts.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

HELPER_SOURCE = '''def _get_guild_event_actor_name(user_id):
    """Resolve a character name for Guild log enrichment.

    A lazy Character System import avoids introducing a module-import cycle.
    Empty, invalid, or unavailable names intentionally produce an empty string,
    so Guild events keep their previous text without exposing a technical ID.
    """
    try:
        from systems.character_system import get_character_name

        actor_name = get_character_name(user_id)
        if actor_name is None:
            return ""

        actor_name = str(actor_name).strip()
        return actor_name
    except Exception:
        return ""
'''

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated contracts for Guild actor-name event logs."""
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
GUILD_PATH = ROOT / "systems" / "guild_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def main():
    before = fingerprint()
    source = GUILD_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(GUILD_PATH))
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "_get_guild_event_actor_name",
            "award_guild_elite_kill",
            "award_guild_contract_completion",
        }
    }
    if len(definitions) != 3:
        fail(f"required Guild functions missing: {sorted(definitions)}")

    helper_source = ast.get_source_segment(
        source, definitions["_get_guild_event_actor_name"]
    ) or ""
    elite_source = ast.get_source_segment(
        source, definitions["award_guild_elite_kill"]
    ) or ""
    contract_source = ast.get_source_segment(
        source, definitions["award_guild_contract_completion"]
    ) or ""

    if "from systems.character_system import get_character_name" not in helper_source:
        fail("actor helper does not use the canonical Character System API")
    if "user_id" in helper_source and "return str(user_id)" in helper_source:
        fail("actor helper exposes technical user_id")
    if "(переміг: {actor_name})" not in elite_source:
        fail("elite event actor suffix missing")
    if 'str(_get_guild_event_actor_name(user_id) or "").strip()' not in elite_source:
        fail("elite actor name is not normalized at the use site")
    if "(виконав: {actor_name})" not in contract_source:
        fail("contract event actor suffix missing")
    if 'str(_get_guild_event_actor_name(user_id) or "").strip()' not in contract_source:
        fail("contract actor name is not normalized at the use site")

    from systems import guild_system as guild

    originals = {
        "get_user_guild_member": guild.get_user_guild_member,
        "add_user_guild_progress": guild.add_user_guild_progress,
        "_get_guild_event_actor_name": guild._get_guild_event_actor_name,
    }
    captured = []

    try:
        guild.get_user_guild_member = lambda user_id: {
            "guild_id": 777,
            "user_id": user_id,
        }

        def fake_add(**kwargs):
            captured.append(kwargs)
            return {
                "success": True,
                "exp": kwargs.get("exp"),
                "resource": kwargs.get("resource"),
                "kills": kwargs.get("kills"),
                "contracts": kwargs.get("contracts"),
            }

        guild.add_user_guild_progress = fake_add
        guild._get_guild_event_actor_name = lambda user_id: "  Audit Hero  "

        elite_result = guild.award_guild_elite_kill(
            -90121331,
            mob={"name": "⭐️ Елітний 🔮 Audit cultist"},
        )
        contract_result = guild.award_guild_contract_completion(
            -90121332,
            contract={"target_mob_name": "🔮 Audit cultist"},
        )

        if elite_result.get("success") is not True:
            fail(f"named elite result failed: {elite_result}")
        if contract_result.get("success") is not True:
            fail(f"named contract result failed: {contract_result}")
        if len(captured) != 2:
            fail(f"named progress calls={len(captured)}, expected 2")

        elite_call, contract_call = captured
        expected_elite = (
            "Перемога над елітним мобом: ⭐️ Елітний 🔮 Audit cultist. "
            "(переміг: Audit Hero)"
        )
        expected_contract = (
            "Виконання контракту: 🔮 Audit cultist. "
            "(виконав: Audit Hero)"
        )
        if elite_call.get("reason") != expected_elite:
            fail(f"elite reason mismatch: {elite_call.get('reason')!r}")
        if contract_call.get("reason") != expected_contract:
            fail(f"contract reason mismatch: {contract_call.get('reason')!r}")
        if (elite_call.get("exp"), elite_call.get("resource"), elite_call.get("kills"), elite_call.get("contracts")) != (25, 1, 1, 0):
            fail(f"elite reward formula changed: {elite_call}")
        if (contract_call.get("exp"), contract_call.get("resource"), contract_call.get("kills"), contract_call.get("contracts")) != (50, 3, 0, 1):
            fail(f"contract reward formula changed: {contract_call}")

        captured.clear()
        guild._get_guild_event_actor_name = lambda user_id: ""
        guild.award_guild_elite_kill(
            -90121333,
            mob={"name": "⭐️ Елітний 🔮 Audit cultist"},
        )
        guild.award_guild_contract_completion(
            -90121334,
            contract={"target_mob_name": "🔮 Audit cultist"},
        )
        if len(captured) != 2:
            fail("unnamed fallback did not produce exactly two calls")
        if captured[0].get("reason") != "Перемога над елітним мобом: ⭐️ Елітний 🔮 Audit cultist.":
            fail(f"unnamed elite fallback changed: {captured[0].get('reason')!r}")
        if captured[1].get("reason") != "Виконання контракту: 🔮 Audit cultist.":
            fail(f"unnamed contract fallback changed: {captured[1].get('reason')!r}")
        if any(str(user_id) in call.get("reason", "") for user_id, call in zip((-90121333, -90121334), captured)):
            fail("technical user_id leaked into Guild reason")

    finally:
        for name, value in originals.items():
            setattr(guild, name, value)

    if before != fingerprint():
        fail("game.db changed during isolated contracts")

    print("[OK] Guild actor name log hotfix contracts")
    print("- canonical Character System name resolver: OK")
    print("- contract actor format: OK")
    print("- elite-kill actor format: OK")
    print("- surrounding whitespace normalization: OK")
    print("- unnamed-user fallback: OK")
    print("- technical user_id exposure: 0")
    print("- elite reward formula: 25 EXP / 1 resource / 1 kill")
    print("- contract reward formula: 50 EXP / 3 resource / 1 contract")
    print("- Guild progress calls per event: exactly 1")
    print("- database mutations: 0")


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
            (root / TARGET_REL).is_file()
            and (root / "systems" / "character_system.py").is_file()
            and (root / "tools" / "check_imports.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def function_nodes(source, name):
    tree = ast.parse(source)
    nodes = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    nodes.sort(key=lambda node: node.lineno)
    return nodes


def function_source(source, name):
    nodes = function_nodes(source, name)
    if len(nodes) != 1:
        raise RuntimeError(f"{name}: definitions={len(nodes)}, expected 1")
    return nodes[0], ast.get_source_segment(source, nodes[0]) or ""


def replace_function(source, name, replacement):
    node, _old = function_source(source, name)
    lines = source.splitlines(keepends=True)
    text = replacement.rstrip() + "\n\n"
    lines[node.lineno - 1:node.end_lineno] = [text]
    return "".join(lines)


def insert_helper(source):
    if "def _get_guild_event_actor_name(" in source:
        return source
    node, _elite = function_source(source, "award_guild_elite_kill")
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1:node.lineno - 1] = [HELPER_SOURCE.rstrip() + "\n\n"]
    return "".join(lines)


def rewrite_elite(source):
    _node, old = function_source(source, "award_guild_elite_kill")
    if "(переміг: {actor_name})" in old:
        return source
    old_return = '''    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_ELITE_KILL_EXP_REWARD,
        resource=GUILD_ELITE_KILL_RESOURCE_REWARD,
        kills=1,
        contracts=0,
        reason=f"{GUILD_ELITE_KILL_SCORE_REASON}: {mob_name}."
    )'''
    new_return = '''    actor_name = str(_get_guild_event_actor_name(user_id) or "").strip()
    reason = f"{GUILD_ELITE_KILL_SCORE_REASON}: {mob_name}."
    if actor_name:
        reason += f" (переміг: {actor_name})"

    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_ELITE_KILL_EXP_REWARD,
        resource=GUILD_ELITE_KILL_RESOURCE_REWARD,
        kills=1,
        contracts=0,
        reason=reason
    )'''
    if old.count(old_return) != 1:
        raise RuntimeError("exact elite Guild progress block not found")
    return replace_function(source, "award_guild_elite_kill", old.replace(old_return, new_return, 1))


def rewrite_contract(source):
    _node, old = function_source(source, "award_guild_contract_completion")
    if "(виконав: {actor_name})" in old:
        return source
    old_return = '''    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_CONTRACT_EXP_REWARD,
        resource=GUILD_CONTRACT_RESOURCE_REWARD,
        kills=0,
        contracts=1,
        reason=f"{GUILD_CONTRACT_SCORE_REASON}: {contract_name}."
    )'''
    new_return = '''    actor_name = str(_get_guild_event_actor_name(user_id) or "").strip()
    reason = f"{GUILD_CONTRACT_SCORE_REASON}: {contract_name}."
    if actor_name:
        reason += f" (виконав: {actor_name})"

    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_CONTRACT_EXP_REWARD,
        resource=GUILD_CONTRACT_RESOURCE_REWARD,
        kills=0,
        contracts=1,
        reason=reason
    )'''
    if old.count(old_return) != 1:
        raise RuntimeError("exact contract Guild progress block not found")
    return replace_function(source, "award_guild_contract_completion", old.replace(old_return, new_return, 1))


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME

    tests = [
        TEST_NAME,
        "smoke_test_guild_contract_target_log.py",
        "smoke_test_contract_reward_direct_facade.py",
        "smoke_test_contract_contracts.py",
        "smoke_test_auction_lifecycle_contracts.py",
        "smoke_test_rom_core.py",
        "check_imports.py",
    ]
    for test_name in tests[1:]:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = target.read_text(encoding="utf-8-sig")
    already = (
        "def _get_guild_event_actor_name(" in source
        and "(переміг: {actor_name})" in source
        and "(виконав: {actor_name})" in source
    )

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if already:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        for test_name in tests:
            run_checked(root, tools / test_name, test_name, env)
        return

    updated = insert_helper(source)
    updated = rewrite_elite(updated)
    updated = rewrite_contract(updated)
    ast.parse(updated, filename=str(target))

    helper_nodes = function_nodes(updated, "_get_guild_event_actor_name")
    if len(helper_nodes) != 1:
        fail(f"Actor helper definitions after patch={len(helper_nodes)}, expected 1")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"systems_guild_system.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, code_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    temp = target.with_name(".guild_system.9_0_13h.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, target)
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        for test_name in tests:
            run_checked(root, tools / test_name, test_name, env)

        readiness = subprocess.run(
            [sys.executable, str(tools / "db_cleanup_readiness.py")],
            cwd=root,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        for expected in (
            "duplicates: 0",
            "legacy_refs: 0",
            "unsafe_delete: 0",
            "maybe_cleanup_later: 0",
        ):
            if expected not in readiness.stdout:
                raise RuntimeError(f"readiness missing {expected}")

    except Exception as exc:
        shutil.copy2(code_backup, target)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; Guild System і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Журнал контрактів тепер додає ім’я виконавця.")
    print("✅ Журнал елітних перемог тепер додає ім’я переможця.")
    print("✅ Для порожнього імені збережено старий формат без user_id.")
    print("✅ Guild EXP/resource/kills/contracts formulas не змінено.")
    print("✅ Історичні записи журналу не переписувалися.")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    for test_name in tests:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
