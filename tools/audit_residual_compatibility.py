#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only audit of residual legacy captures and duplicated configuration."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
REPORT = ROOT / "DB_CLEANUP_9_0_13K_RESIDUAL_COMPATIBILITY_AUDIT.md"
EXCLUDED = {".git", ".venv", "venv", "backup", "patch", "__pycache__"}
CANONICAL_MODULES = {
    "data.classes",
    "data.equipment_profiles",
    "data.balance",
}
PREFIXES = ("_legacy_", "_base_")


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


def top_level_assignments(tree):
    result = defaultdict(list)
    for node in tree.body:
        names = []
        value = None
        if isinstance(node, ast.Assign):
            value = node.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = node.value
            names.append(node.target.id)
        for name in names:
            result[name].append({"line": node.lineno, "node": node, "value": value})
    return result


def canonical_exports():
    exports = defaultdict(dict)
    for module_name in sorted(CANONICAL_MODULES):
        path = ROOT / Path(*module_name.split(".")).with_suffix(".py")
        if not path.is_file():
            continue
        _text, tree = parse(path)
        assignments = top_level_assignments(tree)
        for name, definitions in assignments.items():
            for definition in definitions:
                value = definition["value"]
                try:
                    literal = ast.literal_eval(value)
                except Exception:
                    literal = None
                exports[name][module_name] = {
                    "line": definition["line"],
                    "literal": literal,
                }
    return exports


def db_imported_canonical_names(tree):
    imported = defaultdict(list)
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module not in CANONICAL_MODULES:
            continue
        for alias in node.names:
            imported[alias.asname or alias.name].append({
                "module": node.module,
                "source_name": alias.name,
                "line": node.lineno,
            })
    return imported


def parent_map(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def enclosing_function(node, parents):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return None


def project_name_usage(names):
    usages = defaultdict(list)
    if not names:
        return usages
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
                usages[node.id].append({
                    "file": rel.as_posix(),
                    "line": node.lineno,
                    "function": enclosing_function(node, parents),
                })
            elif isinstance(node, ast.Attribute) and node.attr in names:
                usages[node.attr].append({
                    "file": rel.as_posix(),
                    "line": node.lineno,
                    "function": enclosing_function(node, parents),
                    "attribute": True,
                })
    return usages


def source_capture_findings(text, tree):
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and any(node.id.startswith(prefix) for prefix in PREFIXES):
            findings.append({"name": node.id, "line": node.lineno, "kind": "name"})
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if any(value.startswith(prefix) for prefix in PREFIXES):
                findings.append({"name": value, "line": node.lineno, "kind": "string"})
        elif isinstance(node, ast.JoinedStr):
            segment = ast.get_source_segment(text, node) or ""
            if "_legacy_" in segment or "_base_" in segment:
                findings.append({"name": segment, "line": node.lineno, "kind": "dynamic"})
        elif isinstance(node, ast.Subscript):
            segment = ast.get_source_segment(text, node) or ""
            if "globals()" in segment and ("_legacy_" in segment or "_base_" in segment):
                findings.append({"name": segment, "line": node.lineno, "kind": "globals"})
    unique = {}
    for finding in findings:
        unique[(finding["name"], finding["line"], finding["kind"])] = finding
    return sorted(unique.values(), key=lambda item: (item["line"], item["name"]))


def sandbox_runtime_globals():
    with tempfile.TemporaryDirectory(prefix="rom_9_0_13k_") as temp_name:
        temp_dir = Path(temp_name)
        shutil.copy2(DB_PATH, temp_dir / "game.db")
        probe = temp_dir / "probe.py"
        output = temp_dir / "globals.json"
        probe.write_text(
            "import json, sys\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            "import db\n"
            "names = sorted(name for name in vars(db) if name.startswith(('_legacy_', '_base_')))\n"
            f"open({str(output)!r}, 'w', encoding='utf-8').write(json.dumps(names, ensure_ascii=False))\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(probe)], cwd=temp_dir, env=env,
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            fail(f"sandbox import failed: {result.stderr or result.stdout}")
        return json.loads(output.read_text(encoding="utf-8")), result.stdout.strip(), result.stderr.strip()


def main():
    for path in (DB_PATH, DB_PY):
        if not path.is_file():
            fail(f"missing required file: {path}")

    before = fingerprint(DB_PATH)
    db_text, db_tree = parse(DB_PY)
    assignments = top_level_assignments(db_tree)
    imported = db_imported_canonical_names(db_tree)
    exports = canonical_exports()

    overlapping = sorted(set(assignments).intersection(exports))
    duplicated_config = []
    for name in overlapping:
        db_defs = assignments[name]
        canonical = exports[name]
        db_literals = []
        for definition in db_defs:
            try:
                literal = ast.literal_eval(definition["value"])
            except Exception:
                literal = None
            db_literals.append({"line": definition["line"], "literal": literal})
        duplicated_config.append({
            "name": name,
            "db_definitions": db_literals,
            "canonical": canonical,
            "also_imported_into_db": imported.get(name, []),
        })

    capture_findings = source_capture_findings(db_text, db_tree)
    static_capture_names = sorted({
        item["name"] for item in capture_findings
        if item["kind"] in {"name", "string"}
        and isinstance(item["name"], str)
        and item["name"].startswith(PREFIXES)
    })
    runtime_names, sandbox_stdout, sandbox_stderr = sandbox_runtime_globals()
    all_capture_names = sorted(set(static_capture_names).union(runtime_names))
    usages = project_name_usage(set(all_capture_names))

    capture_classification = []
    for name in all_capture_names:
        entries = usages.get(name, [])
        external = [entry for entry in entries if entry["file"] != "db.py"]
        db_reads = [entry for entry in entries if entry["file"] == "db.py"]
        capture_classification.append({
            "name": name,
            "runtime_present": name in runtime_names,
            "db_reads": db_reads,
            "external_reads": external,
            "candidate": (
                "externally_referenced" if external
                else "db_runtime_dependency" if len(db_reads) > 1
                else "capture_only_or_unreferenced"
            ),
        })

    config_names = {item["name"] for item in duplicated_config}
    config_usages = project_name_usage(config_names)
    for item in duplicated_config:
        item["usages"] = config_usages.get(item["name"], [])
        item["classification"] = (
            "local_definition_and_canonical_import"
            if item["also_imported_into_db"]
            else "same_name_as_canonical_export"
        )

    after = fingerprint(DB_PATH)
    if before != after:
        fail("real game.db changed during audit")

    capture_counts = Counter(item["candidate"] for item in capture_classification)
    config_counts = Counter(item["classification"] for item in duplicated_config)
    report = [
        "# ROM 9.0.13k — Residual Compatibility Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Safety",
        "",
        "- Gameplay files changed: **0**",
        "- Real database rows changed: **0**",
        f"- Real database SHA/size/mtime unchanged: **{before == after}**",
        "- Runtime globals inspected through a sandbox copy of `game.db`.",
        "",
        "## Legacy and base captures",
        "",
        f"- Static source findings: **{len(capture_findings)}**",
        f"- Runtime `_legacy_*` / `_base_*` globals: **{len(runtime_names)}**",
        f"- Unique capture names classified: **{len(capture_classification)}**",
        f"- Classification counts: `{dict(capture_counts)}`",
        f"- Sandbox import stdout: `{sandbox_stdout}`",
        f"- Sandbox import stderr: `{sandbox_stderr}`",
        "",
    ]
    for item in capture_classification:
        report.extend([
            f"### `{item['name']}`",
            "",
            f"- Runtime present: **{item['runtime_present']}**",
            f"- Classification: **{item['candidate']}**",
            f"- Reads in `db.py`: `{item['db_reads']}`",
            f"- Reads outside `db.py`: `{item['external_reads']}`",
            "",
        ])

    report.extend([
        "## Canonical configuration overlap",
        "",
        f"- Overlapping top-level names: **{len(duplicated_config)}**",
        f"- Classification counts: `{dict(config_counts)}`",
        "",
    ])
    for item in duplicated_config:
        report.extend([
            f"### `{item['name']}`",
            "",
            f"- Classification: **{item['classification']}**",
            f"- Local `db.py` definitions: `{item['db_definitions']}`",
            f"- Canonical exports: `{item['canonical']}`",
            f"- Canonical imports into `db.py`: `{item['also_imported_into_db']}`",
            f"- Project reads: `{item['usages']}`",
            "",
        ])

    safe_capture_candidates = [
        item["name"] for item in capture_classification
        if item["candidate"] == "capture_only_or_unreferenced"
    ]
    dependent_captures = [
        item["name"] for item in capture_classification
        if item["candidate"] != "capture_only_or_unreferenced"
    ]
    safe_config_candidates = [
        item["name"] for item in duplicated_config
        if item["classification"] == "local_definition_and_canonical_import"
    ]

    report.extend([
        "## Cleanup groups",
        "",
        f"- Capture-only/unreferenced candidates: `{safe_capture_candidates}`",
        f"- Captures requiring dependency review: `{dependent_captures}`",
        f"- Local config definitions shadowed/replaced by canonical imports: `{safe_config_candidates}`",
        "",
        "## Recommended next steps",
        "",
        "1. Do not mass-delete all `_legacy_*` or `_base_*` symbols.",
        "2. Remove only capture-only/unreferenced names after a targeted runtime contract test.",
        "3. Preserve captures with reads in `db.py` until their callers are redirected to direct system APIs.",
        "4. Treat any external read as a compatibility contract requiring a dedicated migration.",
        "5. Move canonical `data.*` imports before consumers, then remove only local definitions that are demonstrably shadowed.",
        "6. Split the physical cleanup into small patches by domain: Player, Refine/Equipment, and constants.",
        "7. Finish with compile/import, gameplay contracts, and real-user snapshot checks.",
        "",
        "## Suggested patch sequence",
        "",
        "- `patch_9_0_13l_capture_only_cleanup.py`",
        "- `patch_9_0_13m_constants_canonicalization_audit.py`",
        "- `patch_9_0_13n_final_closure_audit.py`",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] residual compatibility audit")
    print(f"- static capture findings: {len(capture_findings)}")
    print(f"- runtime legacy/base globals: {len(runtime_names)}")
    print(f"- capture-only/unreferenced candidates: {len(safe_capture_candidates)}")
    print(f"- captures requiring dependency review: {len(dependent_captures)}")
    print(f"- canonical config overlaps: {len(duplicated_config)}")
    print(f"- shadowed/canonical-import config candidates: {len(safe_config_candidates)}")
    print("- gameplay mutations: 0")
    print("- real database mutations: 0")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
