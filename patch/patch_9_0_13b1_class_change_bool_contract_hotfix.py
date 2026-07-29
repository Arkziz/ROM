#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13b1: fix class-change handler contracts after Character System refactor."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13b1"
TARGET_REL = Path("handlers") / "start.py"
TEST_NAME = "smoke_test_class_change_handler_contract.py"

OLD_BLOCK = '''        consume_result = consume_class_change_available(user_id)

        bot.answer_callback_query(call.id)

        if not consume_result["success"]:
            bot.send_message(
                call.message.chat.id,
                consume_result["message"]
            )
            return

        unequip_result = unequip_incompatible_items_after_class_change(user_id)
        unequip_text = build_class_change_unequip_text_local(unequip_result)

        bot.send_message(
            call.message.chat.id,
            (
                f"🔮 Клас змінено.\\n\\n"
                f"Було: {old_class}\\n"
                f"Стало: {result['class_name']}"
                f"{unequip_text}"
            )
        )
'''

NEW_BLOCK = '''        consume_result = consume_class_change_available(user_id)

        bot.answer_callback_query(call.id)

        # Character System returns bool for consume_class_change_available().
        # Keep compatibility with a possible historical dict result as well.
        if isinstance(consume_result, dict):
            consume_success = bool(consume_result.get("success"))
            consume_message = consume_result.get(
                "message",
                "❌ Не вдалося використати право на зміну класу."
            )
        else:
            consume_success = bool(consume_result)
            consume_message = "❌ Не вдалося використати право на зміну класу."

        if not consume_success:
            bot.send_message(
                call.message.chat.id,
                consume_message
            )
            return

        unequip_result = unequip_incompatible_items_after_class_change(user_id)
        unequip_text = build_class_change_unequip_text_local(unequip_result)
        new_class_name = (
            result.get("class_name")
            or get_character_class_display(user_id)
            or result.get("class_key")
            or class_key
        )

        bot.send_message(
            call.message.chat.id,
            (
                f"🔮 Клас змінено.\\n\\n"
                f"Було: {old_class}\\n"
                f"Стало: {new_class_name}"
                f"{unequip_text}"
            )
        )
'''

TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural/runtime contracts for the class-change callback hotfix."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "handlers" / "start.py"
CHARACTER = ROOT / "systems" / "character_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    start_source = START.read_text(encoding="utf-8-sig")
    start_tree = ast.parse(start_source, filename=str(START))
    character_source = CHARACTER.read_text(encoding="utf-8-sig")
    character_tree = ast.parse(character_source, filename=str(CHARACTER))

    change_nodes = [
        node for node in ast.walk(start_tree)
        if isinstance(node, ast.FunctionDef) and node.name == "change_class"
    ]
    if len(change_nodes) != 1:
        fail(f"change_class definitions={len(change_nodes)}, expected 1")
    change_source = ast.get_source_segment(start_source, change_nodes[0]) or ""

    required = (
        "isinstance(consume_result, dict)",
        "consume_success = bool(consume_result)",
        "result.get(\"class_name\")",
        "get_character_class_display(user_id)",
        "unequip_incompatible_items_after_class_change(user_id)",
    )
    for marker in required:
        if marker not in change_source:
            fail(f"change_class missing marker: {marker}")
    if 'consume_result["success"]' in change_source:
        fail("unsafe dict-only consume_result access remains")
    if "result['class_name']" in change_source:
        fail("unsafe class_name indexing remains")

    consume_nodes = [
        node for node in character_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "consume_class_change_available"
    ]
    if len(consume_nodes) != 1:
        fail("Character System consume function count is not 1")
    consume_source = ast.get_source_segment(character_source, consume_nodes[0]) or ""
    if "return changed" not in consume_source:
        fail("Character System consume contract is no longer bool")

    set_nodes = [
        node for node in character_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "set_character_class"
    ]
    if len(set_nodes) != 1:
        fail("Character System set_character_class count is not 1")
    set_source = ast.get_source_segment(character_source, set_nodes[0]) or ""
    if '"class_key": key' not in set_source:
        fail("set_character_class class_key result contract missing")

    # Pure contract matrix: no DB or Telegram calls.
    samples = (
        (True, True),
        (False, False),
        ({"success": True}, True),
        ({"success": False, "message": "x"}, False),
    )
    for value, expected in samples:
        actual = bool(value.get("success")) if isinstance(value, dict) else bool(value)
        if actual is not expected:
            fail(f"consume compatibility matrix failed: {value!r}")

    print("[OK] class change handler contract hotfix")
    print("- bool consume result: supported")
    print("- historical dict consume result: supported")
    print("- class_key-only set result: supported")
    print("- incompatible equipment auto-unequip path: preserved")
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
        if (root / TARGET_REL).is_file() and (root / "systems" / "character_system.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    test_path = root / "tools" / TEST_NAME
    source = target.read_text(encoding="utf-8-sig")

    already_fixed = (
        "isinstance(consume_result, dict)" in source
        and 'result.get("class_name")' in source
        and 'consume_result["success"]' not in source
    )
    if already_fixed:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        run_checked(root, test_path, TEST_NAME, env)
        run_checked(root, root / "tools" / "smoke_test_character_mutation_contracts.py", "character contracts", env)
        run_checked(root, root / "tools" / "check_imports.py", "check_imports", env)
        return

    if source.count(OLD_BLOCK) != 1:
        fail("Не знайдено точний проблемний блок change_class; файли не змінено.")
    updated = source.replace(OLD_BLOCK, NEW_BLOCK, 1)
    ast.parse(updated, filename=str(target))

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"handlers_start.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, code_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        target.write_text(updated, encoding="utf-8")
        test_path.write_text(TEST, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)
        run_checked(root, test_path, TEST_NAME, env)
        run_checked(root, root / "tools" / "smoke_test_character_mutation_contracts.py", "character contracts", env)
        run_checked(root, root / "tools" / "smoke_test_rom_core.py", "ROM core", env)
        run_checked(root, root / "tools" / "check_imports.py", "check_imports", env)
    except Exception as exc:
        shutil.copy2(code_backup, target)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; handlers/start.py і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ change_class підтримує bool-контракт consume_class_change_available().")
    print("✅ Збережено сумісність зі старим dict-контрактом.")
    print("✅ Виправлено наступний потенційний збій через відсутній result['class_name'].")
    print("✅ Автоматичне зняття несумісного спорядження збережено.")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print(f"   python ./tools/{TEST_NAME}")
    print("   python ./tools/smoke_test_character_mutation_contracts.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")


if __name__ == "__main__":
    main()
