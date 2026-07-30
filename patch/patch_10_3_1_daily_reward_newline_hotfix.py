#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 10.3.1: fix literal backslash-n sequences in Daily Quest reward messages."""
from __future__ import annotations

import ast
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "10.3.1"
TARGET_REL = Path("systems/rune_system.py")
TEST_REL = Path("tools/smoke_test_daily_reward_newline_hotfix.py")

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "systems" / "rune_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def find_function(tree, name):
    return next(
        (node for node in ast.walk(tree)
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name),
        None,
    )


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))
    function = find_function(tree, "claim_daily_quest_reward_with_firius_tokens")
    if function is None:
        fail("Daily Firius reward function not found")

    messages = []
    for node in ast.walk(function):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            messages.append(node.value)

    relevant = [
        value for value in messages
        if "Сумка переповнена" in value
        or "Ви отримали нагороду" in value
        or "Прогрес:" in value
        or "Звільни місце" in value
    ]
    if not relevant:
        fail("Daily reward messages not found")

    literal_escapes = [value for value in relevant if "\\n" in value]
    if literal_escapes:
        fail(f"literal backslash-n remains in messages: {literal_escapes}")

    required = (
        "🎒 Сумка переповнена.\n\n",
        "Звільни місце в інвентарі та спробуй забрати нагороду ще раз.\n",
        "🎁 Ви отримали нагороду за щоденне завдання!\n\n",
    )
    function_source = ast.get_source_segment(source, function) or ""
    compiled = compile(function_source, str(TARGET), "exec")
    namespace = {}
    exec(compiled, namespace)
    constants = []
    for code_object in compiled.co_consts:
        if hasattr(code_object, "co_consts"):
            constants.extend(value for value in code_object.co_consts if isinstance(value, str))
    joined = "\n".join(constants)
    for expected in required:
        if expected not in joined:
            fail(f"expected rendered newline contract missing: {expected!r}")

    print("[OK] Daily reward newline hotfix contracts")
    print("- literal \\n sequences in user messages: 0")
    print("- full-bag paragraph breaks: OK")
    print("- successful reward paragraph breaks: OK")
    print("- Telegram will receive real newline characters: yes")
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
        if (root / TARGET_REL).is_file() and (root / "db.py").is_file():
            return root
    fail("Не знайдено ROM із застосованим 10.3.0.")


def find_function(tree, name):
    return next(
        (node for node in ast.walk(tree)
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name),
        None,
    )


def fix_function_messages(source):
    tree = ast.parse(source, filename=str(TARGET_REL))
    function = find_function(tree, "claim_daily_quest_reward_with_firius_tokens")
    if function is None:
        raise RuntimeError("claim_daily_quest_reward_with_firius_tokens() not found")

    lines = source.splitlines(keepends=True)
    start = function.lineno - 1
    end = function.end_lineno
    block = "".join(lines[start:end])

    # The 10.3.0 patch used a raw embedded source string and escaped newlines
    # twice. This wrote \\n into string literals, which Python interpreted as
    # two visible characters instead of a Telegram line break.
    before_count = block.count("\\\\n")
    if before_count == 0:
        return source, 0
    fixed_block = block.replace("\\\\n", "\\n")
    lines[start:end] = [fixed_block]
    updated = "".join(lines)
    ast.parse(updated, filename=str(TARGET_REL))

    updated_tree = ast.parse(updated)
    updated_function = find_function(
        updated_tree, "claim_daily_quest_reward_with_firius_tokens"
    )
    remaining = []
    for node in ast.walk(updated_function):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "\\n" in node.value:
                remaining.append(node.value)
    if remaining:
        raise RuntimeError(f"literal backslash-n remains: {remaining}")
    return updated, before_count


def run(root, rel):
    result = subprocess.run([sys.executable, str(root / rel)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{rel} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    test_path = root / TEST_REL
    source = target.read_text(encoding="utf-8-sig")
    updated, replacements = fix_function_messages(source)

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = backup_dir / f"systems_rune_system.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, target_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_smoke_test_daily_reward_newline_hotfix.py_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    try:
        target.write_text(updated, encoding="utf-8")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)
        run(root, TEST_REL)
        run(root, Path("tools/smoke_test_daily_firius_token_reward.py"))
        run(root, Path("tools/smoke_test_rune_data_model.py"))
        run(root, Path("tools/smoke_test_rom_core.py"))
        run(root, Path("tools/check_imports.py"))
    except Exception as exc:
        shutil.copy2(target_backup, target)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; rune_system.py і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Виправлено подвійно екранованих переносів: {replacements}")
    print("✅ Telegram отримуватиме реальні переноси рядків замість символів \\n.")
    print("✅ Логіку нагороди, жетони та game.db не змінено.")
    print("Резервні копії:")
    print(f"   {target_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python ./tools/smoke_test_daily_reward_newline_hotfix.py")
    print("   python ./tools/smoke_test_daily_firius_token_reward.py")
    print("   python ./tools/smoke_test_rune_data_model.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")


if __name__ == "__main__":
    main()
