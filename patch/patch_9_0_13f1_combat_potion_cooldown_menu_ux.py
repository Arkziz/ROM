#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13f1: keep the potion menu open during shared cooldown."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13f1"
TARGET_REL = Path("handlers") / "combat.py"
TEST_NAME = "smoke_test_combat_potion_cooldown_menu_ux.py"
TESTS = (
    TEST_NAME,
    "smoke_test_combat_mana_potion_contracts.py",
    "smoke_test_player_combat_stats.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

TURN_HELPER = '''def format_combat_turns_uk(value):
    """Return a Ukrainian turn count with correct plural form."""
    try:
        value = max(0, int(value))
    except Exception:
        value = 0

    mod_10 = value % 10
    mod_100 = value % 100

    if mod_10 == 1 and mod_100 != 11:
        word = "хід"
    elif mod_10 in (2, 3, 4) and mod_100 not in (12, 13, 14):
        word = "ходи"
    else:
        word = "ходів"

    return f"{value} {word}"
'''

NEW_KEYBOARD = '''def build_combat_potion_kb(user_id, cooldown=0):
    items = get_inventory_detailed(user_id)
    profile_summary = get_character_profile_summary(user_id)
    uses_mana = profile_summary.get("resource_type") == "mana"

    try:
        cooldown = max(0, int(cooldown or 0))
    except Exception:
        cooldown = 0

    kb = types.InlineKeyboardMarkup()
    found = False

    for item in items:
        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            quantity,
            max_stack,
            durability,
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef,
            sell_price
        ) = item

        is_hp_potion = type_ in ("potion_hp", "potion_hp_medium")
        is_mp_potion = type_ in ("potion_mp", "potion_mp_medium")

        if category != "potion" or not (is_hp_potion or (uses_mana and is_mp_potion)):
            continue

        found = True

        if cooldown > 0:
            button_text = (
                f"⏳ {name} x{quantity}, "
                f"доступно через {format_combat_turns_uk(cooldown)}"
            )
        else:
            potion_cooldown = (
                5 if type_ in ("potion_hp_medium", "potion_mp_medium") else 3
            )
            button_text = (
                f"{name} x{quantity} — "
                f"cooldown {format_combat_turns_uk(potion_cooldown)}"
            )

        kb.add(types.InlineKeyboardButton(
            text=button_text,
            callback_data=f"combat_potion_{inv_id}"
        ))

    if not found:
        return None

    kb.add(types.InlineKeyboardButton(
        text="⬅️ Назад до бою",
        callback_data="combat_back"
    ))

    return kb
'''

TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contracts for shared potion cooldown menu UX."""
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DB_PATH = ROOT / "game.db"
COMBAT_PATH = ROOT / "handlers" / "combat.py"


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
    source = COMBAT_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(COMBAT_PATH))
    names = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "format_combat_turns_uk",
            "build_combat_potion_kb",
            "choose_potion_in_combat",
            "use_selected_potion_in_combat",
        }
    }
    if len(names) != 4:
        fail(f"required function set incomplete: {sorted(names)}")

    choose_source = ast.get_source_segment(source, names["choose_potion_in_combat"]) or ""
    use_source = ast.get_source_segment(source, names["use_selected_potion_in_combat"]) or ""
    if "if cooldown > 0" in choose_source:
        fail("potion menu is still blocked before rendering")
    if "build_combat_potion_kb(user_id, cooldown=cooldown)" not in choose_source:
        fail("potion menu does not receive shared cooldown")
    if "if cooldown > 0" not in use_source:
        fail("potion use callback no longer blocks use during cooldown")
    if "format_combat_turns_uk(cooldown)" not in use_source:
        fail("use callback does not use Ukrainian turn pluralization")

    from handlers import combat

    expected = {
        0: "0 ходів",
        1: "1 хід",
        2: "2 ходи",
        3: "3 ходи",
        4: "4 ходи",
        5: "5 ходів",
        11: "11 ходів",
        12: "12 ходів",
        21: "21 хід",
        22: "22 ходи",
    }
    for value, text in expected.items():
        actual = combat.format_combat_turns_uk(value)
        if actual != text:
            fail(f"pluralization {value}: {actual!r}, expected {text!r}")

    original_inventory = combat.get_inventory_detailed
    original_profile = combat.get_character_profile_summary
    try:
        combat.get_inventory_detailed = lambda user_id: [
            (1, 201, "🔴 Мале зілля здоров’я", "potion_hp", "common", "potion", 3, 10, 100, 0,0,0,0,0,0,0,1.0),
            (2, 202, "🔵 Мале зілля мани", "potion_mp", "common", "potion", 2, 10, 100, 0,0,0,0,0,0,0,1.2),
        ]
        combat.get_character_profile_summary = lambda user_id: {"resource_type": "mana"}
        kb = combat.build_combat_potion_kb(-1, cooldown=3)
        texts = [button.text for row in kb.keyboard for button in row]
        if "⏳ 🔴 Мале зілля здоров’я x3, доступно через 3 ходи" not in texts:
            fail(f"HP cooldown label missing: {texts}")
        if "⏳ 🔵 Мале зілля мани x2, доступно через 3 ходи" not in texts:
            fail(f"MP cooldown label missing: {texts}")
        if "⬅️ Назад до бою" not in texts:
            fail("back button missing")

        combat.get_character_profile_summary = lambda user_id: {"resource_type": "rage"}
        nonmana = combat.build_combat_potion_kb(-1, cooldown=3)
        nonmana_texts = [button.text for row in nonmana.keyboard for button in row]
        if any("зілля мани" in text for text in nonmana_texts):
            fail(f"MP potion visible to non-mana class: {nonmana_texts}")
    finally:
        combat.get_inventory_detailed = original_inventory
        combat.get_character_profile_summary = original_profile

    if before != fingerprint():
        fail("game.db changed during isolated contracts")

    print("[OK] Combat potion cooldown menu UX contracts")
    print("- shared HP/MP cooldown: preserved")
    print("- menu opens during cooldown: OK")
    print("- individual potion callbacks remain blocked: OK")
    print("- cooldown shown on each potion button: OK")
    print("- Ukrainian 1/2/3/4/5 turn forms: OK")
    print("- MP potions hidden from non-mana classes: OK")
    print("- back-to-combat action: preserved")
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
        if (root / TARGET_REL).is_file() and (root / "tools" / "check_imports.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def function_nodes(source, name):
    tree = ast.parse(source)
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
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
    indent = " " * node.col_offset
    replacement_lines = replacement.rstrip().splitlines()
    if node.col_offset:
        replacement_lines = [indent + line if line else "" for line in replacement_lines]
    text = "\n".join(replacement_lines) + "\n\n"
    lines[node.lineno - 1:node.end_lineno] = [text]
    return "".join(lines)


def insert_helper(source):
    if "def format_combat_turns_uk(" in source:
        return source
    node, _function = function_source(source, "get_potion_cooldown_turns_by_inventory_id")
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1:node.lineno - 1] = [TURN_HELPER.rstrip() + "\n\n"]
    return "".join(lines)


def rewrite_choose_handler(source):
    node, old = function_source(source, "choose_potion_in_combat")
    old_block = '''        cooldown = mob.get("potion_cooldown", 0)

        if cooldown > 0:
    
            bot.send_message(
                message.chat.id,
                f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход.",
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return

        kb = build_combat_potion_kb(user_id)
'''
    new_block = '''        cooldown = mob.get("potion_cooldown", 0)
        kb = build_combat_potion_kb(user_id, cooldown=cooldown)
'''
    if old_block not in old:
        # Support a partially edited but still pre-hotfix variant.
        if "if cooldown > 0:" not in old:
            if "build_combat_potion_kb(user_id, cooldown=cooldown)" in old:
                return source
            raise RuntimeError("choose_potion_in_combat has an unknown structure")
        raise RuntimeError("exact choose-potion cooldown block not found")
    replacement = old.replace(old_block, new_block, 1)
    return replace_function(source, "choose_potion_in_combat", replacement)


def rewrite_use_handler(source):
    _node, old = function_source(source, "use_selected_potion_in_combat")
    old_cooldown = 'f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход."'
    new_cooldown = 'f"🔴 Повний шлунок: зілля можна буде випити через {format_combat_turns_uk(cooldown)}."'
    old_started = 'f"🔴 Повний шлунок: {cooldown_turns} ход.\\n\\n"'
    new_started = 'f"🔴 Повний шлунок: {format_combat_turns_uk(cooldown_turns)}.\\n\\n"'
    if old_cooldown in old:
        old = old.replace(old_cooldown, new_cooldown, 1)
    elif "format_combat_turns_uk(cooldown)" not in old:
        raise RuntimeError("use callback cooldown rejection text not found")
    if old_started in old:
        old = old.replace(old_started, new_started, 1)
    elif "format_combat_turns_uk(cooldown_turns)" not in old:
        raise RuntimeError("use callback started-cooldown text not found")
    return replace_function(source, "use_selected_potion_in_combat", old)


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME

    for test_name in TESTS[1:]:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}. Спочатку має бути застосований 9.0.13f.")

    source = target.read_text(encoding="utf-8-sig")
    if (
        'is_mp_potion = type_ in ("potion_mp", "potion_mp_medium")' not in source
        or 'resource == "mp"' not in source
    ):
        fail("9.0.13f MP potion implementation не знайдено. Спочатку застосуй базовий patch 9.0.13f.")

    already = (
        "def format_combat_turns_uk(" in source
        and "build_combat_potion_kb(user_id, cooldown=cooldown)" in source
        and "доступно через {format_combat_turns_uk(cooldown)}" in source
    )

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if already:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST, encoding="utf-8")
        for name in TESTS:
            run_checked(root, tools / name, name, env)
        return

    updated = insert_helper(source)
    updated = replace_function(updated, "build_combat_potion_kb", NEW_KEYBOARD)
    updated = rewrite_choose_handler(updated)
    updated = rewrite_use_handler(updated)
    ast.parse(updated, filename=str(target))

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"handlers_combat.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, code_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    try:
        target.write_text(updated, encoding="utf-8")
        test_path.write_text(TEST, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)
        for name in TESTS:
            run_checked(root, tools / name, name, env)
    except Exception as exc:
        shutil.copy2(code_backup, target)
        if test_backup:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; Combat handler і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Спільний HP/MP potion cooldown збережено.")
    print("✅ Меню зіль відкривається під час cooldown.")
    print("✅ Кожне зілля показує залишок cooldown у кнопці.")
    print("✅ Використання зілля блокується на callback-рівні.")
    print("✅ Додано правильні форми: хід / ходи / ходів.")
    print("✅ MP-зілля лишаються прихованими для неманових класів.")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    if test_backup:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    for name in TESTS:
        print(f"   python ./tools/{name}")


if __name__ == "__main__":
    main()
