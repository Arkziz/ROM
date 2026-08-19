#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "handlers" / "auction_house.py"


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports_json = any(
        isinstance(node, ast.Import) and any(alias.name == "json" for alias in node.names)
        for node in tree.body
    )
    require(imports_json, "top-level import json is missing")

    helpers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_auction_lot_typed_name_17_1_0"
    ]
    require(len(helpers) == 1, "auction lot typed-name helper count must be exactly one")

    namespace = {"json": json}
    helper_source = ast.get_source_segment(source, helpers[0])
    exec(helper_source, namespace)
    helper = namespace["_auction_lot_typed_name_17_1_0"]

    lot = {
        "item_name": "🔵 Обладунок 8 рівня",
        "category": "equipment",
        "item_snapshot_json": json.dumps({"armor_type": "cloth"}, ensure_ascii=False),
    }
    typed = helper(lot)
    require(typed == "🔵 Обладунок [Тканина] 8 рівня", f"unexpected typed label: {typed!r}")
    require("💠" not in typed, "rune count must not appear in list labels")

    label_paths = source.count("_auction_lot_typed_name_17_1_0(lot)")
    require(label_paths >= 5, f"expected at least five list-label paths, found {label_paths}")
    print("[PASS] Stage 17.1.0.1 auction list type JSON parsing")


if __name__ == "__main__":
    main()
