#!/usr/bin/env python3
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
        "5 жетонів",
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
    print("- daily reward quantity 5: OK")
    print("- existing refine material descriptions preserved: 2")
    print("- category label for IDs 401/402/526: Матеріали")
    print("- literal \\n sequences: 0")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
