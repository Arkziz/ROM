#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "handlers/attribute_allocation.py"
source = path.read_text(encoding="utf-8-sig")
tree = ast.parse(source)
assignments = {}
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = node.value
full = ast.literal_eval(assignments["ATTRIBUTE_LABELS"])
short = ast.literal_eval(assignments["ATTRIBUTE_BUTTON_LABELS"])
assert full == {
    "strength": "Сила",
    "dexterity": "Спритність",
    "intelligence": "Інтелект",
    "wisdom": "Мудрість",
    "stamina": "Витривалість",
}
assert short == {
    "strength": "Сила",
    "dexterity": "Сприт.",
    "intelligence": "Інтел.",
    "wisdom": "Мудр.",
    "stamina": "Витрив.",
}
assert "Очки буде розподілено лише після натискання «Підтвердити»." in source
assert "Зміни застосуються атомарно" not in source
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
keyboard = ast.get_source_segment(source, functions["attribute_allocation_kb"]) or ""
text_builder = ast.get_source_segment(source, functions["build_attribute_allocation_text"]) or ""
assert "ATTRIBUTE_BUTTON_LABELS[name]" in keyboard
assert "ATTRIBUTE_LABELS[name]" in text_builder
assert "ATTRIBUTE_BUTTON_LABELS[name]" not in text_builder
assert 'callback_data="attr:back"' in keyboard
assert 'callback_data="attr:cancel"' in keyboard
print("[PASS] Stage 18.16.5b player-friendly attribute UI text contract")
