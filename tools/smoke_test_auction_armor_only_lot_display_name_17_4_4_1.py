#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "handlers" / "auction_house.py"
source = SOURCE.read_text(encoding="utf-8")
tree = ast.parse(source)
nodes = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "_auction_lot_typed_name_17_1_0"
]
assert len(nodes) == 1, len(nodes)
function_source = ast.get_source_segment(source, nodes[0])

profiles = types.ModuleType("data.equipment_profiles")
profiles.ARMOR_TYPE_LABELS = {
    "cloth": "Тканина", "leather": "Шкіра",
    "chain": "Кольчуга", "plate": "Лати",
}
profiles.ITEM_SUBTYPE_LABELS = {
    "staff_2h": "Дворучний посох",
    "shield": "Щит",
    "talisman": "Магічний талісман",
}
sys.modules["data.equipment_profiles"] = profiles
namespace = {"json": json}
exec(function_source, namespace)
format_name = namespace["_auction_lot_typed_name_17_1_0"]

def lot(name, slot_key, armor_type="", item_subtype=""):
    return {
        "item_name": name,
        "category": "equipment",
        "item_snapshot_json": json.dumps({
            "slot_key": slot_key,
            "armor_type": armor_type,
            "item_subtype": item_subtype,
        }, ensure_ascii=False),
    }

assert format_name(lot("🟢 Наплічники 7 рівня", "shoulders", "cloth")) == "🟢 Наплічники [Тканина] 7 рівня"
assert format_name(lot("⚪ Обладунок [Тканина] 8 рівня [+5]", "chest", "cloth")) == "⚪ Обладунок [Тканина] 8 рівня [+5]"
assert format_name(lot("⚪ Дворучний посох 8 рівня [+10]", "main_hand", "cloth", "staff_2h")) == "⚪ Дворучний посох 8 рівня [+10]"
assert format_name(lot("⚪ Дворучний посох [Дворучний посох] 8 рівня [+10]", "main_hand", "cloth", "staff_2h")) == "⚪ Дворучний посох 8 рівня [+10]"
assert format_name(lot("⚪ Амулет [Тканина] 8 рівня", "necklace", "cloth")) == "⚪ Амулет 8 рівня"
assert format_name(lot("🟢 Кільце [Тканина] 7 рівня", "ring", "cloth")) == "🟢 Кільце 7 рівня"
assert format_name(lot("🔵 Щит [Щит] 9 рівня", "off_hand", "plate", "shield")) == "🔵 Щит 9 рівня"
assert source.count("ROM 17.4.4.1 AUCTION ARMOR-ONLY LOT DISPLAY NAME") == 1
assert "slot_key not in armor_slots" in function_source
assert "ITEM_SUBTYPE_LABELS.get(item_subtype)" in function_source
print("[PASS] Stage 17.4.4.1 auction armor-only lot display name")
