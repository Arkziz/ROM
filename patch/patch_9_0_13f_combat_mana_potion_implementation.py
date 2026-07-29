#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13f: implement mana potions in combat."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13f"
POTION_REL = Path("systems") / "potion_system.py"
COMBAT_REL = Path("handlers") / "combat.py"
TEST_NAME = "smoke_test_combat_mana_potion_contracts.py"
TESTS = (
    TEST_NAME,
    "smoke_test_player_combat_stats.py",
    "smoke_test_player_contracts.py",
    "smoke_test_inventory_refine_contracts.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

NEW_USE_POTION = '''def use_potion_from_inventory(user_id, inventory_id):
    """Use a supported HP or MP potion from one inventory stack."""
    entry = get_inventory_entry(user_id, inventory_id)

    if not entry:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено в інвентарі"
        }

    inv_id, item_id, name, item_type, category, quantity = entry

    if category != "potion":
        return {
            "success": False,
            "message": "❌ Це не зілля"
        }

    potion = POTIONS.get(item_id)

    if not potion:
        return {
            "success": False,
            "message": "❌ Це зілля ще не підтримується"
        }

    if potion["type"] == "mp":
        mp_data = get_user_mp(user_id)
        current_mp = int(mp_data.get("mp", mp_data.get("current_mp", 0)) or 0)
        max_mp = int(mp_data.get("max_mp", 0) or 0)

        if max_mp <= 0:
            return {
                "success": False,
                "message": "🔵 Твій клас не використовує ману"
            }

        if current_mp >= max_mp:
            return {
                "success": False,
                "message": "🔵 Мана вже повна"
            }

        new_mp = min(max_mp, current_mp + int(potion["restore"]))
        real_restore = new_mp - current_mp

        consumed = consume_inventory_item(user_id, inventory_id, 1)
        if not consumed:
            return {
                "success": False,
                "message": "❌ Не вдалося використати зілля"
            }

        set_user_mp(user_id, new_mp)

        return {
            "success": True,
            "resource": "mp",
            "message": (
                f"{potion['name']} використано.\\n"
                f"🔵 Відновлено: +{real_restore} MP\\n"
                f"🔵 Мана: {new_mp}/{max_mp}"
            ),
            "restore_mp": real_restore,
            "new_mp": new_mp,
            "max_mp": max_mp
        }

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    if current_hp >= max_hp:
        return {
            "success": False,
            "message": "❤️ Здоров’я вже повне"
        }

    healed_amount = potion["restore"]
    new_hp = min(max_hp, current_hp + healed_amount)
    real_heal = new_hp - current_hp

    consumed = consume_inventory_item(user_id, inventory_id, 1)

    if not consumed:
        return {
            "success": False,
            "message": "❌ Не вдалося використати зілля"
        }

    set_current_hp(user_id, new_hp)

    return {
        "success": True,
        "resource": "hp",
        "message": (
            f"{potion['name']} використано.\\n"
            f"❤️ Відновлено: +{real_heal} HP\\n"
            f"❤️ Здоров’я: {new_hp}/{max_hp}"
        ),
        "heal": real_heal,
        "new_hp": new_hp,
        "max_hp": max_hp
    }
'''

NEW_COOLDOWN = '''def get_potion_cooldown_turns_by_inventory_id(inventory_id):
    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        return 3

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
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

    if type_ in ("potion_hp_medium", "potion_mp_medium"):
        return 5

    if type_ in ("potion_hp", "potion_mp"):
        return 3

    return 3
'''

NEW_KEYBOARD = '''def build_combat_potion_kb(user_id):
    items = get_inventory_detailed(user_id)
    profile_summary = get_character_profile_summary(user_id)
    uses_mana = profile_summary.get("resource_type") == "mana"

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
        cooldown = 5 if type_ in ("potion_hp_medium", "potion_mp_medium") else 3

        kb.add(types.InlineKeyboardButton(
            text=f"{name} x{quantity} — cooldown {cooldown} ход.",
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

OLD_EMPTY_MESSAGE = '"❌ У тебе немає зілля здоров’я"'
NEW_EMPTY_MESSAGE = '"❌ У тебе немає доступних зіль"'

OLD_RESULT_BLOCK = '''        player_hp = potion_result["new_hp"]
        player_max_hp = potion_result["max_hp"]

        # Оновлюємо здоров'я в mob
        mob["player_hp"] = player_hp
        mob["player_max_hp"] = player_max_hp

        class_resource_text = get_class_resource_line(mob)

        text = (
            f"🧪 ЗІЛЛЯ\\n\\n"
            f"{potion_result['message']}\\n\\n"
            f"✅ Хід не витрачено — {mob['name']} не атакує після використання зілля.\\n"
            f"🔴 Повний шлунок: {cooldown_turns} ход.\\n\\n"
            f"❤️ {character_name}: {player_hp}/{player_max_hp}\\n"
            f"{hp_bar(player_hp, player_max_hp)}\\n"
            f"{class_resource_text}\\n"
            f"👹 {mob['name']}: {mob['hp']}/{mob['max_hp']}\\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )
'''

NEW_RESULT_BLOCK = '''        resource = potion_result.get("resource", "hp")

        if resource == "mp":
            mob["player_mp"] = potion_result["new_mp"]
            mob["player_max_mp"] = potion_result["max_mp"]
        else:
            player_hp = potion_result["new_hp"]
            player_max_hp = potion_result["max_hp"]
            mob["player_hp"] = player_hp
            mob["player_max_hp"] = player_max_hp

        player_hp = mob.get("player_hp", get_current_hp(user_id))
        player_max_hp = mob.get("player_max_hp", get_max_hp(user_id))
        class_resource_text = get_class_resource_line(mob)

        text = (
            f"🧪 ЗІЛЛЯ\\n\\n"
            f"{potion_result['message']}\\n\\n"
            f"✅ Хід не витрачено — {mob['name']} не атакує після використання зілля.\\n"
            f"🔴 Повний шлунок: {cooldown_turns} ход.\\n\\n"
            f"❤️ {character_name}: {player_hp}/{player_max_hp}\\n"
            f"{hp_bar(player_hp, player_max_hp)}\\n"
            f"{class_resource_text}\\n"
            f"👹 {mob['name']}: {mob['hp']}/{mob['max_hp']}\\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )
'''

TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated contracts for Combat Mana Potion implementation."""
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DB_PATH = ROOT / "game.db"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return hashlib.sha256(DB_PATH.read_bytes()).hexdigest(), DB_PATH.stat().st_size, DB_PATH.stat().st_mtime_ns


def main():
    before = fingerprint()
    from systems import potion_system as potion
    from handlers import combat

    originals = {
        "get_inventory_entry": potion.get_inventory_entry,
        "consume_inventory_item": potion.consume_inventory_item,
        "get_current_hp": potion.get_current_hp,
        "get_max_hp": potion.get_max_hp,
        "set_current_hp": potion.set_current_hp,
        "get_user_mp": potion.get_user_mp,
        "set_user_mp": potion.set_user_mp,
        "get_inventory_detailed": combat.get_inventory_detailed,
        "get_character_profile_summary": combat.get_character_profile_summary,
        "get_item_by_inventory_id_full": combat.get_item_by_inventory_id_full,
    }
    consumed = []
    written_mp = []
    written_hp = []
    entries = {
        1: (1, 202, "🔵 Мале зілля мани", "potion_mp", "potion", 2),
        2: (2, 204, "🔵 Середнє зілля мани", "potion_mp_medium", "potion", 1),
        3: (3, 201, "🔴 Мале зілля здоров’я", "potion_hp", "potion", 2),
    }
    try:
        potion.get_inventory_entry = lambda user_id, inventory_id: entries.get(inventory_id)
        potion.consume_inventory_item = lambda user_id, inventory_id, quantity: consumed.append((inventory_id, quantity)) or True
        potion.get_user_mp = lambda user_id: {"mp": 20, "max_mp": 100}
        potion.set_user_mp = lambda user_id, value: written_mp.append(value)
        potion.get_current_hp = lambda user_id: 50
        potion.get_max_hp = lambda user_id: 170
        potion.set_current_hp = lambda user_id, value: written_hp.append(value)

        small = potion.use_potion_from_inventory(-1, 1)
        if small.get("resource") != "mp" or small.get("restore_mp") != 40 or small.get("new_mp") != 60:
            fail(f"small MP contract failed: {small}")
        medium = potion.use_potion_from_inventory(-1, 2)
        if medium.get("resource") != "mp" or medium.get("restore_mp") != 80 or medium.get("new_mp") != 100:
            fail(f"medium MP clamp failed: {medium}")
        hp = potion.use_potion_from_inventory(-1, 3)
        if hp.get("resource") != "hp" or hp.get("new_hp") != 100 or hp.get("heal") != 50:
            fail(f"HP compatibility failed: {hp}")
        if consumed != [(1, 1), (2, 1), (3, 1)]:
            fail(f"consume exactly once failed: {consumed}")

        before_full = list(consumed)
        potion.get_user_mp = lambda user_id: {"mp": 100, "max_mp": 100}
        full = potion.use_potion_from_inventory(-1, 1)
        if full.get("success") is not False or consumed != before_full:
            fail("full MP must not consume potion")

        # Keyboard visibility and cooldowns.
        items = [
            (1, 202, "MP small", "potion_mp", "common", "potion", 2, 10, 100, 0,0,0,0,0,0,0,1.2),
            (2, 204, "MP medium", "potion_mp_medium", "common", "potion", 1, 10, 100, 0,0,0,0,0,0,0,3.6),
            (3, 201, "HP small", "potion_hp", "common", "potion", 2, 10, 100, 0,0,0,0,0,0,0,1.0),
        ]
        combat.get_inventory_detailed = lambda user_id: items
        combat.get_character_profile_summary = lambda user_id: {"resource_type": "mana"}
        mana_kb = combat.build_combat_potion_kb(-1)
        mana_callbacks = [button.callback_data for row in mana_kb.keyboard for button in row]
        if not {"combat_potion_1", "combat_potion_2", "combat_potion_3"}.issubset(set(mana_callbacks)):
            fail(f"mana keyboard missing potions: {mana_callbacks}")
        combat.get_character_profile_summary = lambda user_id: {"resource_type": "rage"}
        nonmana_kb = combat.build_combat_potion_kb(-1)
        nonmana_callbacks = [button.callback_data for row in nonmana_kb.keyboard for button in row]
        if "combat_potion_1" in nonmana_callbacks or "combat_potion_2" in nonmana_callbacks:
            fail(f"MP potion visible to non-mana class: {nonmana_callbacks}")

        def full_item(type_):
            return (1, 999, "x", type_, "common", "potion", None, 1, 1, 10, 100, 0,0,0,0,0,0,0,1.0)
        for type_, expected in (("potion_mp", 3), ("potion_mp_medium", 5), ("potion_hp", 3), ("potion_hp_medium", 5)):
            combat.get_item_by_inventory_id_full = lambda inventory_id, value=full_item(type_): value
            actual = combat.get_potion_cooldown_turns_by_inventory_id(1)
            if actual != expected:
                fail(f"cooldown {type_}={actual}, expected {expected}")

        combat_source = (ROOT / "handlers" / "combat.py").read_text(encoding="utf-8-sig")
        if 'resource == "mp"' not in combat_source or 'mob["player_mp"]' not in combat_source:
            fail("combat callback MP synchronization missing")
        if "Хід не витрачено" not in combat_source:
            fail("turn-free potion rule missing")
    finally:
        for name, value in originals.items():
            module = potion if hasattr(potion, name) and name in {
                "get_inventory_entry", "consume_inventory_item", "get_current_hp", "get_max_hp",
                "set_current_hp", "get_user_mp", "set_user_mp"
            } else combat
            setattr(module, name, value)

    if before != fingerprint():
        fail("game.db changed during isolated contracts")
    print("[OK] Combat Mana Potion implementation contracts")
    print("- small MP restore: 40")
    print("- medium MP restore/clamp: OK")
    print("- full mana no-consume: OK")
    print("- consume exactly once: OK")
    print("- HP potion compatibility: OK")
    print("- mana-class keyboard visibility: OK")
    print("- non-mana-class hiding: OK")
    print("- cooldown small/medium: 3/5")
    print("- combat MP state synchronization: OK")
    print("- potion use spends no turn: OK")
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
        if (root / POTION_REL).is_file() and (root / COMBAT_REL).is_file():
            return root
    fail("Не знайдено корінь ROM.")


def function_node(source, name):
    tree = ast.parse(source)
    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise RuntimeError(f"{name}: definitions={len(nodes)}, expected 1")
    return nodes[0]


def replace_function(source, name, replacement):
    node = function_node(source, name)
    lines = source.splitlines(keepends=True)
    indent = " " * node.col_offset
    replacement_lines = replacement.rstrip().splitlines()
    if node.col_offset:
        replacement_lines = [indent + line if line else "" for line in replacement_lines]
    text = "\n".join(replacement_lines) + "\n\n"
    lines[node.lineno - 1:node.end_lineno] = [text]
    return "".join(lines)


def add_db_imports(source):
    if "    get_user_mp," in source and "    set_user_mp," in source:
        return source
    marker = "    get_max_hp,\n"
    if marker not in source:
        raise RuntimeError("potion_system db import marker not found")
    return source.replace(marker, marker + "    get_user_mp,\n    set_user_mp,\n", 1)


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    potion_path = root / POTION_REL
    combat_path = root / COMBAT_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME
    for test_name in TESTS[1:]:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    potion_source = potion_path.read_text(encoding="utf-8-sig")
    combat_source = combat_path.read_text(encoding="utf-8-sig")
    already = (
        '"resource": "mp"' in potion_source
        and 'is_mp_potion = type_ in ("potion_mp", "potion_mp_medium")' in combat_source
        and 'resource == "mp"' in combat_source
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

    updated_potion = add_db_imports(potion_source)
    updated_potion = replace_function(updated_potion, "use_potion_from_inventory", NEW_USE_POTION)
    updated_combat = replace_function(combat_source, "get_potion_cooldown_turns_by_inventory_id", NEW_COOLDOWN)
    updated_combat = replace_function(updated_combat, "build_combat_potion_kb", NEW_KEYBOARD)
    if updated_combat.count(OLD_EMPTY_MESSAGE) != 1:
        fail("Не знайдено точне HP-only empty message.")
    updated_combat = updated_combat.replace(OLD_EMPTY_MESSAGE, NEW_EMPTY_MESSAGE, 1)
    if updated_combat.count(OLD_RESULT_BLOCK) != 1:
        fail("Не знайдено точний HP-only callback result block.")
    updated_combat = updated_combat.replace(OLD_RESULT_BLOCK, NEW_RESULT_BLOCK, 1)
    ast.parse(updated_potion)
    ast.parse(updated_combat)

    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    potion_backup = backup_dir / f"systems_potion_system.py_{PATCH_ID}_{stamp}.bak"
    combat_backup = backup_dir / f"handlers_combat.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(potion_path, potion_backup)
    shutil.copy2(combat_path, combat_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    try:
        potion_path.write_text(updated_potion, encoding="utf-8")
        combat_path.write_text(updated_combat, encoding="utf-8")
        test_path.write_text(TEST, encoding="utf-8")
        py_compile.compile(str(potion_path), doraise=True)
        py_compile.compile(str(combat_path), doraise=True)
        py_compile.compile(str(test_path), doraise=True)
        for name in TESTS:
            run_checked(root, tools / name, name, env)
        readiness = subprocess.run(
            [sys.executable, str(tools / "db_cleanup_readiness.py")], cwd=root, env=env,
            text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        for expected in ("duplicates: 0", "legacy_refs: 0", "unsafe_delete: 0", "maybe_cleanup_later: 0"):
            if expected not in readiness.stdout:
                raise RuntimeError(f"readiness missing {expected}")
    except Exception as exc:
        shutil.copy2(potion_backup, potion_path)
        shutil.copy2(combat_backup, combat_path)
        if test_backup:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; Potion/Combat файли і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ MP-зілля 202/204 реалізовано в Potion System.")
    print("✅ MP-зілля показуються в бою лише mana-класам.")
    print("✅ MP бойового стану синхронізується після використання.")
    print("✅ Cooldown мале/середнє: 3/5 ходів; хід не витрачається.")
    print("✅ Поточна поведінка HP-зілля збережена.")
    print("Резервні копії:")
    print(f"   {potion_backup.relative_to(root)}")
    print(f"   {combat_backup.relative_to(root)}")
    if test_backup:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    for name in TESTS:
        print(f"   python ./tools/{name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
