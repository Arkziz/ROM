"""Non-recursive AST gate for ROM V2 -> V1 runtime isolation."""
from __future__ import annotations

import ast
import json
from pathlib import Path

from rom_v2.app.v1_reference_isolation import IsolationDecision, classify_module_import

_DYNAMIC_IMPORT_NAMES = {"__import__", "import_module"}


def _module_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return (node.module or "",)
    return ()


def scan(root: Path) -> dict[str, object]:
    violations: list[dict[str, object]] = []
    scanned = 0
    for path in sorted((root / "rom_v2").rglob("*.py")):
        scanned += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module_name in _module_names(node):
                result = classify_module_import(module_name)
                if result.decision is IsolationDecision.DENY:
                    violations.append({
                        "file": path.relative_to(root).as_posix(),
                        "line": getattr(node, "lineno", 0),
                        "module": module_name,
                        "reason": result.reason,
                    })
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in _DYNAMIC_IMPORT_NAMES and node.args:
                    first = node.args[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        result = classify_module_import(first.value)
                        if result.decision is IsolationDecision.DENY:
                            violations.append({
                                "file": path.relative_to(root).as_posix(),
                                "line": getattr(node, "lineno", 0),
                                "module": first.value,
                                "reason": "dynamic_" + result.reason,
                            })
    return {
        "stage": "21.16.3a",
        "status": "PASS" if not violations else "FAIL",
        "scanned_python_files": scanned,
        "violations": violations,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = scan(root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
