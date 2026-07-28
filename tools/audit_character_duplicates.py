#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i5c: verify Character physical cleanup."""
from __future__ import annotations
import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = (
    "normalize_character_name", "validate_character_name", "get_character_name",
    "set_character_name", "get_character_class", "set_character_class",
    "get_character_class_display", "get_character_resource_type", "get_max_mp",
    "get_user_mp", "set_user_mp", "refresh_user_mp",
    "grant_class_change_available", "consume_class_change_available",
    "has_class_change_available",
)
PRESERVE = (
    "get_class_change_available", "is_character_name_taken",
    "needs_character_name", "needs_character_class",
)
REPORT = ROOT / "DB_CLEANUP_9_0_12I5C_CHARACTER_PHYSICAL_CLEANUP.md"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return text, result


def safe(function, *args):
    try:
        return True, function(*args)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main():
    db_text, db_defs = parse(ROOT / "db.py")
    system_text, system_defs = parse(ROOT / "systems" / "character_system.py")

    import db
    from systems import character_system as character

    for name in TARGETS:
        if len(db_defs.get(name, [])) != 1:
            fail(f"db.py {name}: definitions={len(db_defs.get(name, []))}, expected 1")
        if len(system_defs.get(name, [])) < 1:
            fail(f"character_system.py missing {name}")
        wrapper = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        if "character_system" not in wrapper:
            fail(f"db.{name} is not a Character System wrapper")

    for name in PRESERVE:
        if len(db_defs.get(name, [])) != 1:
            fail(f"preserved db helper {name}: definitions={len(db_defs.get(name, []))}")

    if str(inspect.signature(db.set_user_mp)) != "(user_id, mp)":
        fail("public set_user_mp signature changed")
    if str(inspect.signature(character.set_user_mp)) != "(user_id, amount)":
        fail("system set_user_mp signature changed")

    getters = (
        "get_character_name", "get_character_class", "get_character_class_display",
        "get_character_resource_type", "get_max_mp", "get_user_mp",
        "get_class_change_available", "has_class_change_available",
    )
    users = [int(row[0]) for row in db.cursor.execute("SELECT user_id FROM users ORDER BY user_id").fetchall()]
    comparisons = 0
    for user_id in users:
        for name in getters:
            if safe(getattr(db, name), user_id) != safe(getattr(character, name), user_id):
                fail(f"getter mismatch: {name}, user={user_id}")
            comparisons += 1

    samples = ("", "  x  ", "11", "A B")
    pure = 0
    for value in samples:
        for name in ("normalize_character_name", "validate_character_name"):
            if safe(getattr(db, name), value) != safe(getattr(character, name), value):
                fail(f"pure-function mismatch: {name}")
            pure += 1

    report = [
        "# ROM 9.0.12i5c - Character Physical Cleanup",
        "",
        "## Result",
        "",
        f"- Character public wrappers remaining in `db.py`: {len(TARGETS)}",
        "- Earlier Character definitions remaining: 0",
        f"- Read-only getter comparisons: {comparisons}",
        f"- Pure-function comparisons: {pure}",
        "- Mismatches: 0",
        "- Public `set_user_mp(user_id, mp)` signature preserved: yes",
        "- Unique Character helpers preserved: yes",
        "- Database mutations performed by this audit: 0",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] character physical cleanup audit")
    print(f"- public wrappers: {len(TARGETS)}")
    print("- earlier Character definitions: 0")
    print(f"- getter comparisons: {comparisons}")
    print(f"- pure-function comparisons: {pure}")
    print("- mismatches: 0")
    print("- preserved unique helpers: OK")
    print("- database mutations: 0")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
