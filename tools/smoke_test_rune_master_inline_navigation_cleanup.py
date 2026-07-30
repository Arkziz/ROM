#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "handlers" / "runes.py"
KEYBOARDS = ROOT / "keyboards.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def latest_function(tree, name):
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    return sorted(nodes, key=lambda node: node.lineno)[-1] if nodes else None


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))

    home = latest_function(tree, "build_rune_master_home")
    if home is None:
        fail("build_rune_master_home missing")
    home_source = ast.get_source_segment(source, home) or ""
    if "Переробити руни" in home_source or "rf:home:0" in home_source:
        fail("insertion equipment list still contains fusion inline button")

    fusion_home = latest_function(tree, "build_rune_fusion_home")
    if fusion_home is None:
        fail("build_rune_fusion_home missing")
    fusion_home_source = ast.get_source_segment(source, fusion_home) or ""
    if "До Рунного Майстра" in fusion_home_source or "rm:home:0" in fusion_home_source:
        fail("fusion recipe list still contains Rune Master inline back button")

    fusion_handler = latest_function(tree, "register_rune_fusion_handlers")
    if fusion_handler is None:
        fail("register_rune_fusion_handlers missing")
    fusion_handler_source = ast.get_source_segment(source, fusion_handler) or ""
    if "До Рунного Майстра" in fusion_handler_source or "rm:home:0" in fusion_handler_source:
        fail("fusion result still contains Rune Master inline back button")
    if "🔄 До переробки" not in fusion_handler_source:
        fail("fusion result no longer returns to fusion recipes")

    keyboard_source = KEYBOARDS.read_text(encoding="utf-8-sig")
    if 'kb.add("💠 Вставити руну", "🔄 Переробити руни")' not in keyboard_source:
        fail("dedicated Rune Master reply actions missing")
    if 'kb.add("🔙 Ремісничий квартал")' not in keyboard_source:
        fail("Craft District reply back button missing")

    print("[OK] Rune Master inline navigation cleanup contracts")
    print("- insertion list fusion inline button: removed")
    print("- fusion list Rune Master inline button: removed")
    print("- fusion result Rune Master inline button: removed")
    print("- fusion result 'До переробки' button: preserved")
    print("- dedicated reply actions: preserved")
    print("- Craft District reply back button: preserved")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
