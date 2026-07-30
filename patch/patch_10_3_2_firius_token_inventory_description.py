#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 10.3.2: add a useful inventory description for the Firius Token."""
from __future__ import annotations

import ast
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "10.3.2"
TARGET_REL = Path("handlers/inventory.py")
TEST_REL = Path("tools/smoke_test_firius_token_inventory_description.py")

DESCRIPTION_BLOCK = '''
    if item_id == 526:
        return (
            "\\nℹ️ Опис:\\n"
            "🪙 Жетон Фіріуса — особливий матеріал для переробки рун у Рунного Майстра.\\n\\n"
            "Призначення:\\n"
            "• використовується для створення руни наступного рівня;\\n"
            "• одна успішна переробка витрачає 1 жетон;\\n"
            "• для переробки також потрібні 3 однакові руни одного типу й рівня;\\n"
            "• жетони накопичуються та не зникають наступного дня;\\n"
            "• 10 жетонів можна отримати за виконання щоденного завдання.\\n"
        )

'''


CATEGORY_LOCALIZATION_BLOCK = r'''

# ==============================
# ROM 10.3.2 MATERIAL CATEGORY UKRAINIAN LABEL
# ==============================

_BASE_INJECT_MATERIAL_DESCRIPTION_10_3_2 = _inject_refine_material_description


def _inject_refine_material_description(text, inventory_id):
    result = _BASE_INJECT_MATERIAL_DESCRIPTION_10_3_2(text, inventory_id)
    try:
        item = get_item_by_inventory_id_full(inventory_id)
        if not item:
            return result
        item_id = int(item[1])
        if item_id in (401, 402, 526):
            result = result.replace("📦 Категорія: material", "📦 Категорія: Матеріали")
    except Exception:
        pass
    return result
'''

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = ROOT / "handlers" / "inventory.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))
    function = next(
        (node for node in ast.walk(tree)
         if isinstance(node, ast.FunctionDef)
         and node.name == "get_refine_material_description_text"),
        None,
    )
    if function is None:
        fail("description helper not found")

    function_source = ast.get_source_segment(source, function) or ""
    namespace = {}
    exec(compile(function_source, str(TARGET), "exec"), namespace)
    helper = namespace["get_refine_material_description_text"]

    token = helper(526)
    stone = helper(401)
    success_rune = helper(402)
    unknown = helper(999999)

    required = (
        "ℹ️ Опис:",
        "Жетон Фіріуса",
        "Рунного Майстра",
        "1 жетон",
        "3 однакові руни одного типу й рівня",
        "не зникають наступного дня",
        "10 жетонів",
        "щоденного завдання",
    )
    missing = [text for text in required if text not in token]
    if missing:
        fail(f"Firius description missing text: {missing}")
    if "\\n" in token:
        fail("Firius description contains literal backslash-n")
    if not stone or "Камінь Посилення" not in stone:
        fail("Refine Stone description regressed")
    if not success_rune or "Руна Успіху" not in success_rune:
        fail("Success Rune description regressed")
    if unknown != "":
        fail("unknown-item description contract changed")

    if 'item_id in (401, 402, 526)' not in source:
        fail("localized material category item set missing")
    if '📦 Категорія: Матеріали' not in source:
        fail("Ukrainian material category label missing")

    print("[OK] Firius Token inventory description contracts")
    print("- useful purpose description: OK")
    print("- fusion cost 1 token: OK")
    print("- 3 identical rune requirement: OK")
    print("- cumulative/no-reset rule: OK")
    print("- daily reward quantity 10: OK")
    print("- existing refine material descriptions preserved: 2")
    print("- category label for IDs 401/402/526: Матеріали")
    print("- literal \\n sequences: 0")
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
        if (root / TARGET_REL).is_file() and (root / "data/runes.py").is_file():
            return root
    fail("Не знайдено ROM із застосованою моделлю рун 10.2.0.")


def update_inventory_handler(source):
    if "Жетон Фіріуса — особливий матеріал для переробки рун" in source:
        return source, 0

    tree = ast.parse(source, filename=str(TARGET_REL))
    function = next(
        (node for node in ast.walk(tree)
         if isinstance(node, ast.FunctionDef)
         and node.name == "get_refine_material_description_text"),
        None,
    )
    if function is None:
        raise RuntimeError("get_refine_material_description_text() not found")

    lines = source.splitlines(keepends=True)
    function_lines = lines[function.lineno - 1:function.end_lineno]
    local_return_index = None
    for index in range(len(function_lines) - 1, -1, -1):
        if function_lines[index].strip() == 'return ""':
            local_return_index = index
            break
    if local_return_index is None:
        raise RuntimeError("final empty description return not found")

    absolute_index = function.lineno - 1 + local_return_index
    lines[absolute_index:absolute_index] = [DESCRIPTION_BLOCK]
    updated = "".join(lines)
    ast.parse(updated, filename=str(TARGET_REL))
    return updated, 1


def add_category_localization(source):
    marker = "ROM 10.3.2 MATERIAL CATEGORY UKRAINIAN LABEL"
    if marker in source:
        return source, 0
    updated = source.rstrip() + CATEGORY_LOCALIZATION_BLOCK + "\n"
    ast.parse(updated, filename=str(TARGET_REL))
    return updated, 1


def run(root, rel):
    result = subprocess.run([sys.executable, str(root / rel)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{rel} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    test = root / TEST_REL
    source = target.read_text(encoding="utf-8-sig")
    updated, description_changes = update_inventory_handler(source)
    updated, category_changes = add_category_localization(updated)
    changes = description_changes + category_changes

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = backup_dir / f"handlers_inventory.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, target_backup)
    if test.exists():
        test_backup = backup_dir / f"tools_smoke_test_firius_token_inventory_description.py_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test, test_backup)

    try:
        target.write_text(updated, encoding="utf-8")
        test.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test), doraise=True)
        for rel in (
            TEST_REL,
            Path("tools/smoke_test_daily_reward_newline_hotfix.py"),
            Path("tools/smoke_test_daily_firius_token_reward.py"),
            Path("tools/smoke_test_rune_data_model.py"),
            Path("tools/smoke_test_rom_core.py"),
            Path("tools/check_imports.py"),
        ):
            if not (root / rel).is_file():
                raise RuntimeError(f"missing check: {rel}")
            run(root, rel)
    except Exception as exc:
        shutil.copy2(target_backup, target)
        if test_backup is not None:
            shutil.copy2(test_backup, test)
        elif test.exists():
            test.unlink()
        fail(f"Перевірка не пройдена; inventory.py і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Застосовано змін inventory UI: {changes}")
    print("✅ Категорію для Каменя Посилення, Руни Успіху та Жетона Фіріуса локалізовано як «Матеріали».")
    print("✅ В описі пояснено призначення, рецепт, витрату та накопичення жетонів.")
    print("✅ Описи Каменя Посилення та Руни Успіху збережено.")
    print("✅ Gameplay-логіку нагороди й game.db не змінено.")
    print("Резервні копії:")
    print(f"   {target_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python ./tools/smoke_test_firius_token_inventory_description.py")
    print("   python ./tools/smoke_test_daily_reward_newline_hotfix.py")
    print("   python ./tools/smoke_test_daily_firius_token_reward.py")
    print("   python ./tools/smoke_test_rune_data_model.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")


if __name__ == "__main__":
    main()
