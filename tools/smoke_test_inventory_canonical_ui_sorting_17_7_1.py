#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "handlers/inventory.py"
source = SOURCE.read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}

for name in (
    "_inventory_ui_normalized_name_17_7_1",
    "_inventory_ui_category_key_17_7_1",
    "_inventory_ui_sort_key_17_7_1",
):
    assert name in functions, name

category_definitions = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "get_category_items"
]
assert len(category_definitions) >= 4, len(category_definitions)
assert source.count("ROM 17.7.1 INVENTORY CANONICAL UI SORTING") == 1
assert "_STAGE_17_7_1_BASE_GET_CATEGORY_ITEMS = get_category_items" in source

namespace = {}
for name in (
    "_inventory_ui_normalized_name_17_7_1",
    "_inventory_ui_category_key_17_7_1",
    "_inventory_ui_sort_key_17_7_1",
):
    code = ast.get_source_segment(source, functions[name])
    exec(code, namespace)

# Constants required by the extracted functions.
namespace["_STAGE_17_7_1_RARITY_PREFIXES"] = ("⚪️", "⚪", "🟢", "🔵", "🟣")
namespace["_STAGE_17_7_1_CATEGORY_ORDER"] = (
    "main_hand", "off_hand", "helmet", "shoulders", "chest", "gloves",
    "legs", "boots", "necklace", "ring", "trash", "rune", "material", "potion",
)
namespace["_STAGE_17_7_1_CATEGORY_RANK"] = {
    key: index for index, key in enumerate(namespace["_STAGE_17_7_1_CATEGORY_ORDER"])
}

normalize = namespace["_inventory_ui_normalized_name_17_7_1"]
category_key = namespace["_inventory_ui_category_key_17_7_1"]
sort_key = namespace["_inventory_ui_sort_key_17_7_1"]

def item(inv_id, name, category="potion", slot_key="", quantity=1, rarity="common"):
    return (
        inv_id, 1, name, "type", rarity, category, slot_key, 1,
        quantity, 10, 100, 0, 0, 0, 0, 0, 0, 0, 0.0,
    )

assert normalize(item(1, "🟢 Наплічники")) == "наплічники"
assert normalize(item(1, "⚪️ Амулет")) == "амулет"
assert category_key(item(1, "Меч", "equipment", "main_hand")) == "main_hand"

# Alphabetical, case-insensitive, rarity-independent.
values = [
    item(10, "🔵 Сила"),
    item(11, "🟢 витривалість"),
    item(12, "⚪ Амулет"),
]
assert [row[0] for row in sorted(values, key=lambda row: sort_key(row, False))] == [12, 11, 10]

# Equal normalized names: newest inventory ID first; quantity and rarity do not matter.
duplicates = [
    item(87, "⚪ Наплічники", quantity=10, rarity="common"),
    item(690, "🟣 Наплічники", quantity=1, rarity="epic"),
]
assert [row[0] for row in sorted(duplicates, key=lambda row: sort_key(row, False))] == [690, 87]

# The all view preserves logical category rank and sorts only inside each group.
all_values = [
    item(30, "Зілля", "potion"),
    item(20, "Сірий лут", "trash"),
    item(12, "Булава", "equipment", "main_hand"),
    item(13, "Арбалет", "equipment", "main_hand"),
    item(25, "Руна", "rune"),
]
assert [row[0] for row in sorted(all_values, key=lambda row: sort_key(row, True))] == [13, 12, 20, 25, 30]

final_source = ast.get_source_segment(source, category_definitions[-1]) or ""
assert "_STAGE_17_7_1_BASE_GET_CATEGORY_ITEMS" in final_source
assert "include_category=(category_key == \"all\")" in final_source
print("[PASS] Stage 17.7.1 inventory canonical UI sorting")
