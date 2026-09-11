#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository-wide read-only audit of generate_class_shop_equipment."""
from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "game.db"
SHOP = ROOT / "db_modules/shop.py"
DYNAMIC = ROOT / "systems/dynamic_equipment_system.py"
REPORT = ROOT / "reports/stage_18_17_5_legacy_class_shop_generator_audit.json"
MD = ROOT / "MD/STAGE_18_17_5_LEGACY_CLASS_SHOP_GENERATOR_AUDIT.md"
SCAN_DIRS = ("data", "systems", "handlers", "db_modules", "tools")
TARGET = "generate_class_shop_equipment"
MISSING_DEPENDENCY = "generate_equipment_item"


def read(path):
    return path.read_text(encoding="utf-8-sig")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dotted_name(node):
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def function_defs(tree):
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append(node)
    return rows


def call_names(owner):
    names = []
    for node in ast.walk(owner):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name:
                names.append(name)
    return sorted(set(names))


def imported_symbols(owner):
    rows = []
    for node in ast.walk(owner):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                rows.append({
                    "module": node.module,
                    "name": alias.name,
                    "asname": alias.asname,
                    "level": node.level,
                    "lineno": node.lineno,
                })
    return rows


def detects_mutation(owner):
    mutation_tokens = ("INSERT ", "UPDATE ", "DELETE ", "ALTER ", "CREATE TABLE", "DROP TABLE")
    strings = [
        node.value for node in ast.walk(owner)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    sql = sorted({token.strip() for text in strings for token in mutation_tokens if token in text.upper()})
    calls = call_names(owner)
    suspicious_calls = sorted({
        call for call in calls
        if call.split(".")[-1] in {
            "execute", "executemany", "commit", "add_item",
            "create_generated_equipment_item", "create_generated_equipment_item_for_slot",
            "allocate_generated_item_id", "allocate_shop_preview_item_id",
        }
    })
    return {"sql_tokens": sql, "mutation_like_calls": suspicious_calls}


def scan_repository():
    files = []
    definitions = []
    references = []
    exports = []
    callback_references = []
    import_graph = defaultdict(set)

    for folder in SCAN_DIRS:
        base = ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            relative = str(path.relative_to(ROOT))
            try:
                text = read(path)
                tree = ast.parse(text)
            except Exception as error:
                files.append({"file": relative, "parse_error": str(error)})
                continue

            files.append({"file": relative, "parse_error": None})
            module = relative[:-3].replace("\\", ".").replace("/", ".")
            aliases = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imported_module = (node.module or "")
                    for alias in node.names:
                        local = alias.asname or alias.name
                        aliases[local] = f"{imported_module}.{alias.name}" if imported_module else alias.name
                        if alias.name == TARGET:
                            references.append({
                                "file": relative,
                                "kind": "direct_import",
                                "module": imported_module,
                                "lineno": node.lineno,
                            })
                        if alias.name == TARGET and relative.endswith("__init__.py"):
                            exports.append({"file": relative, "kind": "package_import", "lineno": node.lineno})
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        aliases[alias.asname or alias.name.split(".")[-1]] = alias.name

            for node in function_defs(tree):
                if node.name == TARGET:
                    definitions.append({
                        "file": relative,
                        "lineno": node.lineno,
                        "end_lineno": node.end_lineno,
                        "signature": ast.unparse(node.args),
                        "calls": call_names(node),
                        "imports": imported_symbols(node),
                        "mutation": detects_mutation(node),
                        "return_count": sum(isinstance(item, ast.Return) for item in ast.walk(node)),
                    })

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = dotted_name(node.func)
                    local = name.split(".")[0] if name else ""
                    expanded = aliases.get(local, name)
                    if local and name != local and local in aliases:
                        expanded = aliases[local] + name[len(local):]
                    if name == TARGET or expanded.endswith("." + TARGET):
                        references.append({
                            "file": relative,
                            "kind": "call",
                            "name": name,
                            "expanded": expanded,
                            "lineno": node.lineno,
                            "enclosing_function": next((owner.name for owner in function_defs(tree) if owner.lineno <= node.lineno <= owner.end_lineno), None),
                        })
                elif isinstance(node, ast.Constant) and isinstance(node.value, str) and TARGET in node.value:
                    references.append({"file": relative, "kind": "string_reference", "lineno": node.lineno})
                elif isinstance(node, ast.Assign):
                    if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                        try:
                            values = ast.literal_eval(node.value)
                        except Exception:
                            values = []
                        if TARGET in values:
                            exports.append({"file": relative, "kind": "__all__", "lineno": node.lineno})
                elif isinstance(node, ast.Call):
                    pass

            # Telegram registration and callback proximity scan.
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = dotted_name(node.func)
                    if any(token in name for token in ("message_handler", "callback_query_handler", "register_message_handler", "register_callback_query_handler")):
                        segment = ast.get_source_segment(text, node) or ""
                        if TARGET in segment:
                            callback_references.append({"file": relative, "lineno": node.lineno, "registration": name})

            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and node.module:
                    import_graph[module].add(node.module)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        import_graph[module].add(alias.name)

    return {
        "files": files,
        "definitions": definitions,
        "references": references,
        "exports": exports,
        "callback_references": callback_references,
        "import_graph": {key: sorted(value) for key, value in sorted(import_graph.items())},
    }


def database_check():
    before = sha(DB)
    conn = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        result = {
            "quick_check": conn.execute("PRAGMA quick_check").fetchone()[0],
            "foreign_key_violations": conn.execute("PRAGMA foreign_key_check").fetchall(),
            "total_changes": conn.total_changes,
        }
    finally:
        conn.close()
    result.update(sha256_before=before, sha256_after=sha(DB))
    result["unchanged"] = result["sha256_before"] == result["sha256_after"]
    return result


def main():
    for path in (SHOP, DYNAMIC, DB):
        if not path.exists():
            raise RuntimeError(f"Missing required path: {path.relative_to(ROOT)}")

    repository = scan_repository()
    definitions = repository["definitions"]
    references = repository["references"]
    actual_calls = [row for row in references if row["kind"] == "call"]
    direct_imports = [row for row in references if row["kind"] == "direct_import"]
    non_definition_references = [
        row for row in references
        if not (row["kind"] == "string_reference" and row["file"] == str(Path(__file__).relative_to(ROOT)))
    ]

    if len(definitions) != 1:
        raise RuntimeError(f"Expected one {TARGET} definition, found {len(definitions)}")

    owner = definitions[0]
    missing_imports = [
        row for row in owner["imports"]
        if row["module"] == "systems.dynamic_equipment_system" and row["name"] == MISSING_DEPENDENCY
    ]
    mutation = owner["mutation"]
    route_is_runtime_reachable = bool(actual_calls or repository["exports"] or repository["callback_references"])
    route_is_dead_candidate = not route_is_runtime_reachable
    calls_missing_dependency = any(call.split(".")[-1] == MISSING_DEPENDENCY for call in owner["calls"])

    db = database_check()
    status = "PASS"
    if (
        db["quick_check"] != "ok"
        or db["foreign_key_violations"]
        or db["total_changes"] != 0
        or not db["unchanged"]
        or not missing_imports
        or not calls_missing_dependency
    ):
        status = "FAIL"

    recommendation = {
        "classification": "dead_legacy_candidate" if route_is_dead_candidate else "reachable_broken_route",
        "preferred_action": (
            "remove the unreferenced legacy generate_class_shop_equipment function in a scoped mutation patch"
            if route_is_dead_candidate
            else "replace the reachable legacy route with an explicit adapter to the canonical base-shop API after contract approval"
        ),
        "do_not_add_generate_equipment_item_to_dynamic_module": True,
        "reason": "Adding the missing symbol would create or revive a second equipment-generation path outside the canonical generator.",
        "next_patch": (
            "18.17.6 remove dead legacy class-shop generator and add regression"
            if route_is_dead_candidate
            else "18.17.6 adapt reachable legacy class-shop route to canonical shop flow"
        ),
    }

    report = {
        "stage": "18.17.5",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "production_mutation": False,
        "target": TARGET,
        "definition": owner,
        "actual_call_references": actual_calls,
        "direct_import_references": direct_imports,
        "exports": repository["exports"],
        "callback_references": repository["callback_references"],
        "all_non_definition_references": non_definition_references,
        "missing_dependency_imports": missing_imports,
        "calls_missing_dependency": calls_missing_dependency,
        "runtime_reachable": route_is_runtime_reachable,
        "dead_legacy_candidate": route_is_dead_candidate,
        "writes_sql_or_inventory": bool(mutation["sql_tokens"] or mutation["mutation_like_calls"]),
        "database": db,
        "recommendation": recommendation,
    }

    REPORT.parent.mkdir(exist_ok=True)
    MD.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Stage 18.17.5: Legacy Class-Shop Generator Read-only Audit",
        "",
        f"**Status:** {status}",
        "**Production mutation:** none",
        "",
        "## Reachability",
        "",
        f"- Definition count: `{len(definitions)}`.",
        f"- Runtime call references: `{len(actual_calls)}`.",
        f"- Direct imports: `{len(direct_imports)}`.",
        f"- Exports: `{len(repository['exports'])}`.",
        f"- Callback registrations: `{len(repository['callback_references'])}`.",
        f"- Runtime reachable: `{route_is_runtime_reachable}`.",
        f"- Dead legacy candidate: `{route_is_dead_candidate}`.",
        "",
        "## Missing dependency",
        "",
        f"- The route imports `{MISSING_DEPENDENCY}` from `systems.dynamic_equipment_system`.",
        f"- The route calls the missing dependency: `{calls_missing_dependency}`.",
        "",
        "## Side effects",
        "",
        f"- SQL or inventory mutation detected inside the legacy function: `{report['writes_sql_or_inventory']}`.",
        "- The function appears to build and return an in-memory list, but attempts to call a missing generator dependency.",
        "",
        "## Recommendation",
        "",
        f"- Classification: `{recommendation['classification']}`.",
        f"- Preferred action: {recommendation['preferred_action']}.",
        "- Do not add a second `generate_equipment_item` implementation to the compatibility module.",
        "",
        "## Database safety",
        "",
        f"- quick_check: `{db['quick_check']}`.",
        f"- FK violations: `{len(db['foreign_key_violations'])}`.",
        f"- DB unchanged: `{db['unchanged']}`.",
    ]
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if status != "PASS":
        raise RuntimeError("Legacy class-shop audit execution invariants failed")

    print(json.dumps({
        "status": "PASS",
        "runtime_calls": len(actual_calls),
        "direct_imports": len(direct_imports),
        "exports": len(repository["exports"]),
        "callbacks": len(repository["callback_references"]),
        "runtime_reachable": route_is_runtime_reachable,
        "dead_legacy_candidate": route_is_dead_candidate,
        "writes_sql_or_inventory": report["writes_sql_or_inventory"],
        "db_unchanged": db["unchanged"],
        "json": str(REPORT.relative_to(ROOT)),
        "md": str(MD.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
