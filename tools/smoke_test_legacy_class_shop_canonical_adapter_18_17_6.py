#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.equipment_stat_policy import CLASS_ARMOR_TYPES, CLASS_MAIN_HAND_SUBTYPES, CLASS_OFF_HAND_SUBTYPES
from db_modules.shop import generate_class_shop_equipment, populate_class_shop_for_user

CLASSES = ("warrior", "knight", "scout", "rogue", "mage", "priest")
for class_key in CLASSES:
    offers = generate_class_shop_equipment(class_key, 8)
    assert isinstance(offers, list)
    expected_count = 6 + len(CLASS_MAIN_HAND_SUBTYPES[class_key]) + len(CLASS_OFF_HAND_SUBTYPES[class_key])
    assert len(offers) == expected_count
    assert len({(row["slot_key"], row["item_profile"]) for row in offers}) == expected_count
    for row in offers:
        assert row["target_class"] == class_key
        assert row["item_level"] == 8
        assert row["rarity"] == "common"
        assert row["preview_api"] == "create_common_equipment_shop_preview"
        assert set(row) == {"slot_key", "item_profile", "armor_type", "item_level", "rarity", "target_class", "preview_api"}
        if row["slot_key"] in ("helmet", "shoulders", "chest", "gloves", "legs", "boots"):
            assert row["armor_type"] == CLASS_ARMOR_TYPES[class_key]
            assert row["item_profile"] == ""
        elif row["slot_key"] == "main_hand":
            assert row["item_profile"] in CLASS_MAIN_HAND_SUBTYPES[class_key]
            assert row["armor_type"] == ""
        elif row["slot_key"] == "off_hand":
            assert row["item_profile"] in CLASS_OFF_HAND_SUBTYPES[class_key]
            assert row["armor_type"] == ""
        else:
            raise AssertionError(row)

assert generate_class_shop_equipment("mage", 0)[0]["item_level"] == 1
try:
    generate_class_shop_equipment("unknown", 5)
except ValueError:
    pass
else:
    raise AssertionError("unknown class must fail closed")

source = (ROOT / "db_modules/shop.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)
def owner(name):
    rows = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(rows) == 1
    return rows[0]

generate_owner = owner("generate_class_shop_equipment")
populate_owner = owner("populate_class_shop_for_user")
for function in (generate_owner, populate_owner):
    segment = ast.get_source_segment(source, function) or ""
    for forbidden in (
        "generate_equipment_item", "allocate_shop_preview_item_id", "clear_shop_preview_items",
        "cursor.execute", "conn.commit", "INSERT INTO", "UPDATE ", "DELETE FROM",
        "random.", "create_generated_equipment_item",
    ):
        assert forbidden not in segment, (function.name, forbidden)

assert "create_common_equipment_shop_preview" in (ast.get_source_segment(source, generate_owner) or "")
assert callable(populate_class_shop_for_user)
print("[PASS] Stage 18.17.6 legacy class-shop canonical adapter")
