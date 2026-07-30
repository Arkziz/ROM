#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13m: install and run a read-only constants canonicalization audit."""
from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13m"
TOOL_NAME = "audit_constants_canonicalization.py"

TOOL = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only audit for moving duplicated db.py constants to canonical data modules."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
REPORT = ROOT / "DB_CLEANUP_9_0_13M_CONSTANTS_CANONICALIZATION_AUDIT.md"
CANONICAL_MODULES = (
    "data.classes",
    "data.equipment_profiles",
    "data.balance",
)
EXCLUDED = {".git", ".venv", "venv", "backup", "patch", "__pycache__"}


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest(),
        path.stat().st_size,
        path.stat().st_mtime_ns,
    )


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def top_level_definitions(text, tree):
    result = defaultdict(list)
    for node in tree.body:
        names = []
        value = None
        if isinstance(node, ast.Assign):
            value = node.value
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
            value = node.value
        for name in names:
            try:
                literal = ast.literal_eval(value)
                literal_ok = True
            except Exception:
                literal = None
                literal_ok = False
            result[name].append({
                "line": node.lineno,
                "end_line": node.end_lineno,
                "literal_ok": literal_ok,
                "literal": literal,
                "source": ast.get_source_segment(text, node) or "",
            })
    return result


def canonical_definitions():
    result = defaultdict(dict)
    for module in CANONICAL_MODULES:
        path = ROOT / Path(*module.split(".")).with_suffix(".py")
        if not path.is_file():
            fail(f"canonical module missing: {path}")
        text, tree = parse(path)
        definitions = top_level_definitions(text, tree)
        for name, rows in definitions.items():
            if not rows:
                continue
            result[name][module] = rows[-1]
    return result


def parent_map(tree):
    result = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            result[child] = parent
    return result


def enclosing_function(node, parents):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return None


def project_reads(names):
    reads = defaultdict(list)
    if not names:
        return reads
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED for part in rel.parts):
            continue
        try:
            _text, tree = parse(path)
        except Exception:
            continue
        parents = parent_map(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in names:
                reads[node.id].append({
                    "file": rel.as_posix(),
                    "line": node.lineno,
                    "function": enclosing_function(node, parents),
                })
            elif isinstance(node, ast.Attribute) and node.attr in names:
                reads[node.attr].append({
                    "file": rel.as_posix(),
                    "line": node.lineno,
                    "function": enclosing_function(node, parents),
                    "attribute": True,
                })
    return reads


def import_lines(tree):
    rows = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            rows.append({
                "module": node.module,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "names": [alias.asname or alias.name for alias in node.names],
            })
    return rows


def first_read_line(tree, name):
    lines = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == name
    ]
    return min(lines) if lines else None


def sandbox_values(names):
    with tempfile.TemporaryDirectory(prefix="rom_9_0_13m_") as temp_name:
        temp = Path(temp_name)
        shutil.copy2(DB_PATH, temp / "game.db")
        output = temp / "values.json"
        probe = temp / "probe.py"
        probe.write_text(
            "import json, sys\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            "import db\n"
            f"names = {sorted(names)!r}\n"
            "def normalize(value):\n"
            "    try:\n"
            "        json.dumps(value, ensure_ascii=False, sort_keys=True)\n"
            "        return value\n"
            "    except Exception:\n"
            "        return repr(value)\n"
            "payload = {name: normalize(getattr(db, name, None)) for name in names}\n"
            f"open({str(output)!r}, 'w', encoding='utf-8').write(json.dumps(payload, ensure_ascii=False, sort_keys=True))\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(probe)], cwd=temp, env=env,
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            fail(f"sandbox import failed: {result.stderr or result.stdout}")
        return json.loads(output.read_text(encoding="utf-8"))


def comparable(left, right):
    return json.dumps(left, ensure_ascii=False, sort_keys=True, default=str) == json.dumps(
        right, ensure_ascii=False, sort_keys=True, default=str
    )


def main():
    if not DB_PATH.is_file() or not DB_PY.is_file():
        fail("db.py or game.db missing")
    before = fingerprint(DB_PATH)
    db_text, db_tree = parse(DB_PY)
    db_defs = top_level_definitions(db_text, db_tree)
    canonical = canonical_definitions()
    overlaps = sorted(set(db_defs).intersection(canonical))
    reads = project_reads(set(overlaps))
    imports = import_lines(db_tree)
    runtime = sandbox_values(overlaps)

    rows = []
    for name in overlaps:
        local_defs = db_defs[name]
        effective_local = local_defs[-1]
        owners = canonical[name]
        exact_owners = []
        divergent_owners = []
        for module, definition in owners.items():
            if effective_local["literal_ok"] and definition["literal_ok"] and comparable(
                effective_local["literal"], definition["literal"]
            ):
                exact_owners.append(module)
            else:
                divergent_owners.append(module)

        imported = [
            item for item in imports
            if item["module"] in CANONICAL_MODULES and name in item["names"]
        ]
        first_read = first_read_line(db_tree, name)
        owner = exact_owners[0] if len(exact_owners) == 1 else None
        runtime_matches_owner = False
        if owner:
            owner_value = owners[owner]["literal"]
            runtime_matches_owner = comparable(runtime.get(name), owner_value)

        duplicate_local_definitions = len(local_defs) > 1
        safe_shape = bool(
            owner
            and not divergent_owners
            and runtime_matches_owner
            and effective_local["literal_ok"]
            and owners[owner]["literal_ok"]
        )
        classification = (
            "exact_single_owner_candidate" if safe_shape and not duplicate_local_definitions
            else "duplicate_local_definitions" if duplicate_local_definitions
            else "multi_or_divergent_owner" if not owner or divergent_owners
            else "runtime_mismatch"
        )
        rows.append({
            "name": name,
            "classification": classification,
            "owner": owner,
            "exact_owners": exact_owners,
            "divergent_owners": divergent_owners,
            "local_lines": [item["line"] for item in local_defs],
            "canonical_lines": {
                module: definition["line"] for module, definition in owners.items()
            },
            "first_db_read_line": first_read,
            "canonical_imports_in_db": imported,
            "runtime_matches_owner": runtime_matches_owner,
            "reads": reads.get(name, []),
        })

    exact = [row for row in rows if row["classification"] == "exact_single_owner_candidate"]
    duplicate = [row for row in rows if row["classification"] == "duplicate_local_definitions"]
    risky = [row for row in rows if row["classification"] not in {
        "exact_single_owner_candidate", "duplicate_local_definitions"
    }]
    groups = defaultdict(list)
    for row in exact:
        groups[row["owner"]].append(row["name"])

    after = fingerprint(DB_PATH)
    if before != after:
        fail("real game.db changed during audit")

    report = [
        "# ROM 9.0.13m — Constants Canonicalization Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Safety",
        "",
        "- Gameplay files changed: **0**",
        "- Real database rows changed: **0**",
        f"- Real database SHA/size/mtime unchanged: **{before == after}**",
        "- Runtime values were inspected through a sandbox copy of `game.db`.",
        "",
        "## Summary",
        "",
        f"- Overlapping constants: **{len(rows)}**",
        f"- Exact single-owner candidates: **{len(exact)}**",
        f"- Constants with duplicate local definitions: **{len(duplicate)}**",
        f"- Divergent/runtime-risk constants: **{len(risky)}**",
        f"- Candidate groups by canonical module: `{dict(groups)}`",
        "",
        "## Per-constant analysis",
        "",
    ]
    for row in rows:
        report.extend([
            f"### `{row['name']}`",
            "",
            f"- Classification: **{row['classification']}**",
            f"- Canonical owner: `{row['owner']}`",
            f"- Exact owners: `{row['exact_owners']}`",
            f"- Divergent owners: `{row['divergent_owners']}`",
            f"- Local definition lines: `{row['local_lines']}`",
            f"- Canonical definition lines: `{row['canonical_lines']}`",
            f"- First read in `db.py`: `{row['first_db_read_line']}`",
            f"- Existing canonical imports in `db.py`: `{row['canonical_imports_in_db']}`",
            f"- Runtime value matches canonical owner: **{row['runtime_matches_owner']}**",
            f"- Project reads: `{row['reads']}`",
            "",
        ])

    report.extend([
        "## Proposed physical migration plan",
        "",
        "1. Add explicit canonical imports near the beginning of `db.py`, before the first consumer of each constant.",
        "2. Remove only exact local definitions after asserting equality with the canonical export.",
        "3. Handle constants with multiple local definitions separately because the earlier value may differ from the final effective value.",
        "4. Preserve the public `db.<CONSTANT>` surface by importing canonical names directly into the `db` module namespace.",
        "5. Verify runtime identity/value parity for `db`, `data.classes`, `data.equipment_profiles`, and `data.balance`.",
        "6. Run class selection, equipment generation/compatibility, contract, energy/regen, repair, refine, and daily-quest contracts.",
        "7. Compare real-user and database fingerprints before and after all tests.",
        "",
        "## Recommended split",
        "",
        f"- Phase A, exact `data.classes` constants: `{groups.get('data.classes', [])}`",
        f"- Phase B, exact `data.equipment_profiles` constants: `{groups.get('data.equipment_profiles', [])}`",
        f"- Phase C, exact `data.balance` constants: `{groups.get('data.balance', [])}`",
        f"- Manual review before deletion: `{[row['name'] for row in duplicate + risky]}`",
        "",
        "## Conclusion",
        "",
        "The overlap is real, but canonicalization must preserve the `db` module's public constant surface and import order. No constant was removed by this audit.",
        "",
        "Suggested next patch: `patch_9_0_13n_constants_canonicalization_cleanup.py`",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] constants canonicalization audit")
    print(f"- overlapping constants: {len(rows)}")
    print(f"- exact single-owner candidates: {len(exact)}")
    print(f"- duplicate local-definition constants: {len(duplicate)}")
    print(f"- divergent/runtime-risk constants: {len(risky)}")
    print(f"- data.classes candidates: {len(groups.get('data.classes', []))}")
    print(f"- data.equipment_profiles candidates: {len(groups.get('data.equipment_profiles', []))}")
    print(f"- data.balance candidates: {len(groups.get('data.balance', []))}")
    print("- gameplay mutations: 0")
    print("- real database mutations: 0")
    print(f"- report: {REPORT}")


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
            and (root / "game.db").is_file()
            and (root / "data" / "classes.py").is_file()
            and (root / "data" / "equipment_profiles.py").is_file()
            and (root / "data" / "balance.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM або canonical data modules.")


def main():
    root = find_root()
    target = root / "tools" / TOOL_NAME
    backup = None

    if target.exists() and target.read_text(encoding="utf-8-sig") != TOOL:
        backup_dir = root / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backup_dir / f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(target, backup)

    target.write_text(TOOL, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        py_compile.compile(str(target), doraise=True)
        result = subprocess.run(
            [sys.executable, str(target)], cwd=root, env=env, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"audit exit code {result.returncode}")
    except Exception as exc:
        if backup is not None:
            shutil.copy2(backup, target)
        elif target.exists():
            target.unlink()
        fail(f"Аудит не пройдено; встановлення відкочено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Створено: tools/{TOOL_NAME}")
    print("✅ Створено: DB_CLEANUP_9_0_13M_CONSTANTS_CANONICALIZATION_AUDIT.md")
    print("✅ Gameplay-код і реальна game.db не змінені.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root) if backup else 'не потрібні - новий файл'}")
    print("Повторний запуск:")
    print(f"   python ./tools/{TOOL_NAME}")


if __name__ == "__main__":
    main()
