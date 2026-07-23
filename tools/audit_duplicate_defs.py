# ✅ ROM REFACTOR SAFETY AUDIT TOOLS V1
#!/usr/bin/env python3
"""
ROM Refactor Tool: audit duplicate function definitions.

Purpose:
- Find functions/classes defined multiple times in a file or across project files.
- Especially useful before cleaning db.py override/hotfix/final-override blocks.

Usage:
    python tools/audit_duplicate_defs.py
    python tools/audit_duplicate_defs.py db.py
    python tools/audit_duplicate_defs.py db.py handlers/combat.py systems
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_TARGETS = ["db.py"]
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "backup", "patch", "TXT"}


def iter_python_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []

    for target in targets:
        path = Path(target)

        if not path.exists():
            print(f"[WARN] not found: {path}")
            continue

        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue

        if path.is_dir():
            for py_file in path.rglob("*.py"):
                if any(part in EXCLUDED_DIRS for part in py_file.parts):
                    continue
                files.append(py_file)

    return sorted(set(files))


def collect_defs(py_file: Path) -> list[tuple[str, int, str]]:
    try:
        text = py_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = py_file.read_text(encoding="utf-8-sig")

    tree = ast.parse(text, filename=str(py_file))
    result: list[tuple[str, int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append((node.name, node.lineno, "def"))
        elif isinstance(node, ast.ClassDef):
            result.append((node.name, node.lineno, "class"))

    return sorted(result, key=lambda item: item[1])


def main() -> int:
    targets = sys.argv[1:] or DEFAULT_TARGETS
    files = iter_python_files(targets)

    if not files:
        print("No python files found.")
        return 1

    by_name: dict[str, list[tuple[Path, int, str]]] = defaultdict(list)
    duplicates_inside_file: dict[Path, dict[str, list[tuple[int, str]]]] = {}

    for py_file in files:
        file_defs = collect_defs(py_file)
        local: dict[str, list[tuple[int, str]]] = defaultdict(list)

        for name, lineno, kind in file_defs:
            by_name[name].append((py_file, lineno, kind))
            local[name].append((lineno, kind))

        dup_local = {name: rows for name, rows in local.items() if len(rows) > 1}
        if dup_local:
            duplicates_inside_file[py_file] = dup_local

    print("=" * 80)
    print("ROM duplicate definitions audit")
    print("=" * 80)
    print(f"Files scanned: {len(files)}")
    print("")

    if duplicates_inside_file:
        print("[DUPLICATES INSIDE SAME FILE]")
        for py_file, items in duplicates_inside_file.items():
            print(f"\n{py_file}")
            for name, rows in sorted(items.items()):
                places = ", ".join(f"{kind}@{line}" for line, kind in rows)
                print(f"  - {name}: {places}")
    else:
        print("[OK] No duplicate definitions inside scanned files.")

    print("\n" + "=" * 80)
    print("[DUPLICATES ACROSS SCANNED FILES]")
    cross = {name: rows for name, rows in by_name.items() if len(rows) > 1}

    if not cross:
        print("[OK] No duplicate names across scanned files.")
    else:
        for name, rows in sorted(cross.items()):
            print(f"\n{name}")
            for py_file, line, kind in rows:
                print(f"  - {kind} {py_file}:{line}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
