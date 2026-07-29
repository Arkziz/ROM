#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13d: restore target mob names in Guild contract completion logs."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13d"
TARGET_REL = Path("systems") / "guild_system.py"
TEST_NAME = "smoke_test_guild_contract_target_log.py"
TESTS = (
    TEST_NAME,
    "smoke_test_contract_reward_direct_facade.py",
    "smoke_test_contract_contracts.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

OLD_LOOKUP = '''        if isinstance(contract, dict):
            contract_name = contract.get("name") or contract.get("title") or contract.get("contract_name") or contract_name
        elif contract:
            contract_name = str(contract)
'''

NEW_LOOKUP = '''        if isinstance(contract, dict):
            contract_name = (
                contract.get("target_mob_name")
                or contract.get("name")
                or contract.get("title")
                or contract.get("contract_name")
                or contract_name
            )
        elif contract:
            contract_name = str(contract)
'''

TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated Guild contract-target logging contracts."""
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


def db_fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def main():
    before = db_fingerprint()
    source = GUILD_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(GUILD_PATH))
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "award_guild_contract_completion"
    ]
    if len(nodes) != 1:
        fail(f"award_guild_contract_completion definitions={len(nodes)}, expected 1")
    function_source = ast.get_source_segment(source, nodes[0]) or ""
    keys = (
        'contract.get("target_mob_name")',
        'contract.get("name")',
        'contract.get("title")',
        'contract.get("contract_name")',
    )
    for key in keys:
        if key not in function_source:
            fail(f"missing compatibility key: {key}")
    positions = [function_source.index(key) for key in keys]
    if positions != sorted(positions):
        fail("contract name lookup priority is incorrect")

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
            return {
                "success": True,
                "exp": kwargs.get("exp", 0),
                "resource": kwargs.get("resource", 0),
                "contracts": kwargs.get("contracts", 0),
            }

        guild.add_user_guild_progress = fake_add

        cases = (
            (
                {"target_mob_name": "🧙 Audit target", "name": "Wrong fallback"},
                "Виконання контракту: 🧙 Audit target.",
                "target_mob_name",
            ),
            ({"name": "Legacy name"}, "Виконання контракту: Legacy name.", "name"),
            ({"title": "Legacy title"}, "Виконання контракту: Legacy title.", "title"),
            ({"contract_name": "Legacy contract"}, "Виконання контракту: Legacy contract.", "contract_name"),
            ("String contract", "Виконання контракту: String contract.", "string"),
            (None, "Виконання контракту: контракт.", "fallback"),
        )

        for index, (contract, expected_reason, label) in enumerate(cases):
            result = guild.award_guild_contract_completion(
                user_id=-90121310 - index,
                contract=contract,
            )
            if not result or result.get("success") is not True:
                fail(f"{label} result contract failed: {result!r}")
            actual = captured[-1]
            if actual.get("reason") != expected_reason:
                fail(
                    f"{label} reason mismatch: "
                    f"expected={expected_reason!r}, actual={actual.get('reason')!r}"
                )
            if actual.get("contracts") != 1:
                fail(f"{label} Guild contract increment is not 1")
            if actual.get("kills") != 0:
                fail(f"{label} Guild kill increment changed")

    finally:
        guild.get_user_guild_member = original_member
        guild.add_user_guild_progress = original_add

    if len(captured) != 6:
        fail(f"Guild progress calls={len(captured)}, expected 6")
    if before != db_fingerprint():
        fail("game.db changed during isolated contracts")

    print("[OK] Guild contract target log hotfix contracts")
    print("- target_mob_name priority: OK")
    print("- name/title/contract_name compatibility: OK")
    print("- string contract compatibility: OK")
    print("- generic fallback for missing data: OK")
    print("- Guild contracts increment: exactly 1")
    print("- Guild kills increment: 0")
    print("- isolated Guild progress calls: 6")
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
            and (root / "systems" / "contract_system.py").is_file()
            and (root / "tools" / "check_imports.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def function_source(source, name):
    tree = ast.parse(source)
    nodes = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(nodes) != 1:
        raise RuntimeError(f"{name} definitions={len(nodes)}, expected 1")
    return ast.get_source_segment(source, nodes[0]) or ""


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME

    for test_name in TESTS[1:]:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = target.read_text(encoding="utf-8-sig")
    award_source = function_source(source, "award_guild_contract_completion")

    already_fixed = (
        'contract.get("target_mob_name")' in award_source
        and award_source.index('contract.get("target_mob_name")')
        < award_source.index('contract.get("name")')
    )

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if already_fixed:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST, encoding="utf-8")
        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name, env)
        return

    if source.count(OLD_LOOKUP) != 1:
        fail("Не знайдено точний Guild contract-name lookup; файли не змінено.")

    updated = source.replace(OLD_LOOKUP, NEW_LOOKUP, 1)
    updated_award = function_source(updated, "award_guild_contract_completion")
    if 'contract.get("target_mob_name")' not in updated_award:
        fail("Після заміни target_mob_name не знайдено.")
    if updated_award.index('contract.get("target_mob_name")') > updated_award.index('contract.get("name")'):
        fail("target_mob_name не має найвищого пріоритету.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"systems_guild_system.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, code_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    temp = target.with_name(".guild_system.9_0_13d.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, target)
        test_path.write_text(TEST, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        for test_name in TESTS:
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
    print("✅ Guild contract log використовує target_mob_name як головну назву цілі.")
    print("✅ name/title/contract_name збережено як backward-compatible fallback.")
    print("✅ Guild EXP, resource, kills і contracts formulas не змінено.")
    print("✅ Історичні записи журналу не змінювалися.")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
