#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i10c: final Contract Reward physical cleanup."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i10c"
TARGET = "claim_contract_reward"
CAPTURE = "_base_claim_contract_reward_before_guild_reward_v1"
OBSOLETE_HELPERS = (
    "_guild_contract_reward_result_success_v1",
    "_guild_contract_reward_append_message_v1",
)
TEST_NAME = "smoke_test_contract_reward_direct_facade.py"
TESTS = (
    TEST_NAME,
    "smoke_test_contract_contracts.py",
    "smoke_test_player_progression_direct.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

POST_CLEANUP_TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-i10c isolated contracts for the final Contract Reward facade."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

IDS = (-90121021, -90121022, -90121023)
CAPTURE = "_base_claim_contract_reward_before_guild_reward_v1"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def columns(table):
    return [row[1] for row in db.conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def user_tables():
    result = []
    for (name,) in db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        try:
            if "user_id" in columns(name):
                result.append(name)
        except Exception:
            pass
    return result


def cleanup():
    for table in [name for name in user_tables() if name != "users"]:
        for user_id in IDS:
            try:
                db.conn.execute(f'DELETE FROM "{table}" WHERE user_id=?', (user_id,))
            except Exception:
                pass
    for user_id in IDS:
        try:
            db.conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        except Exception:
            pass
    db.conn.commit()


def real_snapshot():
    cols = columns("users")
    select_list = ",".join(f'"{name}"' for name in cols)
    rows = [
        tuple(row)
        for row in db.conn.execute(
            f"SELECT {select_list} FROM users WHERE user_id>=0 ORDER BY user_id"
        ).fetchall()
    ]
    return cols, rows


def create_fixture(user_id, completed, current_kills=0, reward_exp=40):
    db.create_user(user_id)
    db.init_contract_system()
    db.conn.execute(
        "UPDATE users SET level=5, exp=0, daily_contracts_completed=0, daily_contract_date=? WHERE user_id=?",
        (db.get_today_str(), user_id),
    )
    db.conn.execute(
        """INSERT INTO user_active_contracts (
        user_id, created_date, player_level, target_mob_name, target_mob_level,
        target_min_level, target_max_level, target_kills, current_kills,
        reward_exp, completed, reward_claimed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id, db.get_today_str(), 5, "fixture_target", 5,
            1, 10, 5, current_kills, reward_exp, completed, 0,
        ),
    )
    db.conn.commit()


def state(user_id):
    user = db.conn.execute(
        "SELECT level, exp, daily_contracts_completed FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    contract_count = db.conn.execute(
        "SELECT COUNT(*) FROM user_active_contracts WHERE user_id=?",
        (user_id,),
    ).fetchone()[0]
    return tuple(user), int(contract_count)


def main():
    source = (ROOT / "db.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(ROOT / "db.py"))
    definitions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "claim_contract_reward"
    ]
    if len(definitions) != 1:
        fail(f"claim_contract_reward definitions={len(definitions)}, expected 1 after i10c")

    final_source = ast.get_source_segment(source, definitions[0]) or ""
    if "systems.contract_system" not in final_source:
        fail("final db.claim_contract_reward is not a Contract System facade")
    if CAPTURE in source or hasattr(db, CAPTURE):
        fail("obsolete Contract Reward capture still exists")
    for helper in (
        "_guild_contract_reward_result_success_v1",
        "_guild_contract_reward_append_message_v1",
    ):
        if helper in source or hasattr(db, helper):
            fail(f"obsolete helper still exists: {helper}")

    before = real_snapshot()
    cleanup()
    checks = 0
    original_award = db.award_guild_contract_completion
    original_text = db.get_guild_activity_reward_text
    guild_calls = []

    try:
        missing = db.claim_contract_reward(IDS[0])
        if not isinstance(missing, dict) or missing.get("success") is not False:
            fail(f"missing-contract result failed: {missing!r}")
        checks += 1

        create_fixture(IDS[0], completed=0, current_kills=2)
        incomplete_before = state(IDS[0])
        incomplete = db.claim_contract_reward(IDS[0])
        incomplete_after = state(IDS[0])
        if incomplete.get("success") is not False or incomplete_before != incomplete_after:
            fail("incomplete contract changed state")
        checks += 1

        create_fixture(IDS[1], completed=1, current_kills=5, reward_exp=40)

        def fake_award(user_id, contract=None):
            guild_calls.append((user_id, contract))
            return {"success": True, "exp": 50, "resource": 3, "contracts": 1}

        def fake_text(result):
            return "🏰 Fixture Guild reward"

        db.award_guild_contract_completion = fake_award
        db.get_guild_activity_reward_text = fake_text

        completed = db.claim_contract_reward(IDS[1])
        completed_state = state(IDS[1])
        if completed.get("success") is not True:
            fail(f"completed result failed: {completed!r}")
        if int(completed.get("reward_exp", 0)) != 40:
            fail(f"reward_exp mismatch: {completed!r}")
        if completed_state[0][2] != 1 or completed_state[1] != 0:
            fail(f"completed state invalid: {completed_state!r}")
        if len(guild_calls) != 1 or guild_calls[0][0] != IDS[1]:
            fail(f"Guild hook calls invalid: {guild_calls!r}")
        if "Fixture Guild reward" not in str(completed.get("message") or ""):
            fail("Guild reward text was not appended")
        checks += 5

        repeat_before = state(IDS[1])
        repeat = db.claim_contract_reward(IDS[1])
        repeat_after = state(IDS[1])
        if repeat.get("success") is not False:
            fail(f"repeat claim unexpectedly succeeded: {repeat!r}")
        if repeat_before != repeat_after or len(guild_calls) != 1:
            fail("repeat reward protection failed")
        checks += 1

        # Real no-guild path: guild helper must fail safely without changing claim result.
        create_fixture(IDS[2], completed=1, current_kills=5, reward_exp=40)
        db.award_guild_contract_completion = original_award
        db.get_guild_activity_reward_text = original_text
        no_guild = db.claim_contract_reward(IDS[2])
        if no_guild.get("success") is not True or state(IDS[2])[1] != 0:
            fail(f"no-guild completed claim failed: {no_guild!r}")
        checks += 1

    finally:
        db.award_guild_contract_completion = original_award
        db.get_guild_activity_reward_text = original_text
        cleanup()

    if before != real_snapshot():
        fail("real users changed")

    print("[OK] contract reward final post-cleanup contracts")
    print(f"- contract checks: {checks}")
    print("- single public facade: OK")
    print("- obsolete capture/helpers: absent")
    print("- missing/incomplete paths: OK")
    print("- EXP and daily completion: OK")
    print("- active contract deletion: OK")
    print("- Guild hook exactly once: OK")
    print("- no-guild path: OK")
    print("- repeat reward protection: OK")
    print("- fixture cleanup: OK")
    print("- real user mutations: 0")


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
            and (root / "systems" / "contract_system.py").is_file()
            and (root / "tools" / TEST_NAME).is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def function_map(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return result


def node_start(node):
    decorators = getattr(node, "decorator_list", None) or []
    return min([node.lineno] + [decorator.lineno for decorator in decorators])


def run_checked(root, path, label):
    result = subprocess.run([sys.executable, str(path)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    db_path = root / "db.py"
    system_path = root / "systems" / "contract_system.py"
    tools = root / "tools"
    test_path = tools / TEST_NAME
    readiness_path = tools / "db_cleanup_readiness.py"

    for test_name in TESTS:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    definitions = function_map(tree)

    already_clean = (
        len(definitions.get(TARGET, [])) == 1
        and CAPTURE not in source
        and all(helper not in source for helper in OBSOLETE_HELPERS)
    )
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(POST_CLEANUP_TEST, encoding="utf-8")
        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)
        return

    target_nodes = definitions.get(TARGET, [])
    if len(target_nodes) != 2:
        fail(f"db.py claim_contract_reward: definitions={len(target_nodes)}, очікувалося 2.")

    final_source = ast.get_source_segment(source, target_nodes[-1]) or ""
    if "systems.contract_system" not in final_source or CAPTURE in final_source:
        fail("Фінальна claim_contract_reward не є direct Contract System facade після i10b.")

    remove_ranges = []
    early_node = target_nodes[0]
    remove_ranges.append((node_start(early_node), early_node.end_lineno, TARGET))

    capture_blocks = []
    for node in tree.body:
        if isinstance(node, ast.Try):
            names = {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}
            if CAPTURE in names:
                capture_blocks.append(node)
    if len(capture_blocks) != 1:
        fail(f"Contract Reward capture blocks={len(capture_blocks)}, очікувалося 1.")
    capture_node = capture_blocks[0]
    remove_ranges.append((capture_node.lineno, capture_node.end_lineno, CAPTURE))

    removed_helpers = []
    for helper in OBSOLETE_HELPERS:
        nodes = definitions.get(helper, [])
        if len(nodes) != 1:
            fail(f"db.py {helper}: definitions={len(nodes)}, очікувалося 1.")
        helper_node = nodes[0]
        load_count = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id == helper
        )
        if load_count != 0:
            fail(f"Obsolete helper {helper} ще має AST Load usage: {load_count}")
        remove_ranges.append((node_start(helper_node), helper_node.end_lineno, helper))
        removed_helpers.append(helper)

    ordered = sorted(remove_ranges)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            fail(f"Діапазони видалення перетинаються: {previous[2]} / {current[2]}")

    lines = source.splitlines(keepends=True)
    for start, end, _name in sorted(remove_ranges, reverse=True):
        del lines[start - 1:end]
    updated = "".join(lines)

    updated_tree = ast.parse(updated, filename=str(db_path))
    updated_definitions = function_map(updated_tree)
    if len(updated_definitions.get(TARGET, [])) != 1:
        fail(f"Після очищення claim_contract_reward definitions={len(updated_definitions.get(TARGET, []))}")
    retained = ast.get_source_segment(updated, updated_definitions[TARGET][0]) or ""
    if "systems.contract_system" not in retained:
        fail("Після очищення втрачено direct Contract System facade.")
    if CAPTURE in updated:
        fail("Після очищення залишився obsolete capture.")
    for helper in OBSOLETE_HELPERS:
        if helper in updated_definitions or helper in updated:
            fail(f"Після очищення залишився obsolete helper: {helper}")

    duplicates_after = {
        name for name, nodes in updated_definitions.items() if len(nodes) > 1
    }
    if duplicates_after:
        fail(f"Після фінального очищення залишилися duplicates: {sorted(duplicates_after)}")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_contract_reward_cleanup_{stamp}.bak"
    test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    shutil.copy2(test_path, test_backup)

    temp = db_path.with_name(".db.i10c.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_path)
        test_path.write_text(POST_CLEANUP_TEST, encoding="utf-8")

        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(system_path), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)

        readiness = subprocess.run(
            [sys.executable, str(readiness_path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")

        for expected in (
            "definitions: 348",
            "duplicates: 0",
            "legacy_refs: 0",
            "unsafe_delete: 0",
            "maybe_cleanup_later: 0",
        ):
            if expected not in readiness.stdout:
                raise RuntimeError(f"readiness не містить очікуване значення: {expected}")

    except Exception as exc:
        shutil.copy2(db_backup, db_path)
        shutil.copy2(test_backup, test_path)
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; db.py і Contract Reward test відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Фізично видалено ранню claim_contract_reward: 1")
    print("✅ Видалено obsolete Contract Reward capture: 1")
    print(f"✅ Видалено obsolete Guild hook helpers: {len(removed_helpers)}")
    print("✅ Залишено одну direct facade claim_contract_reward.")
    print("✅ Duplicate groups: 0.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./systems/contract_system.py")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
