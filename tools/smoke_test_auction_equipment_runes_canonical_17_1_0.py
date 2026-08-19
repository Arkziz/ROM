#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from systems import auction_house_system as auction

def require(value, message):
    if not value:
        raise AssertionError(message)

def main():
    snapshot = {
        "slot_key": "chest", "armor_type": "cloth",
        "inserted_runes": [{"slot_index": 0, "rune_item_id": 501,
            "rune_stat": "INT", "rune_level": 2,
            "rune_name": "💠 Руна Інтелекту II"}],
    }
    require(auction._auction_equipment_type_line(snapshot) == "🏷 Тип предмета: [Тканина]", "type formatter")
    lines = auction._auction_rune_socket_lines(snapshot)
    require(lines[0] == "💠 Рунічні слоти: 1/3", "socket count")
    require("Слот 1: 💠 Руна Інтелекту II" in lines[1], "inserted rune")
    require(lines[3] == "• Слот 3: порожній", "empty socket")
    source = (ROOT / "systems" / "auction_house_system.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for name in ("get_inventory_item_snapshot_for_auction", "_auction_insert_inventory_from_snapshot",
                 "build_auction_sell_item_review_text", "build_user_auction_lot_details",
                 "build_auction_buy_lot_details_v2"):
        count = sum(isinstance(n, ast.FunctionDef) and n.name == name for n in tree.body)
        require(count >= 1, f"missing {name}")
    print("[PASS] Stage 17.1.0 canonical auction rune preservation")
if __name__ == "__main__":
    main()
