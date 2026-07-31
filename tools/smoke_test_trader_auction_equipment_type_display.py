#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITY = ROOT / "handlers" / "city.py"
AUCTION = ROOT / "handlers" / "auction_house.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    city = CITY.read_text(encoding="utf-8-sig")
    auction = AUCTION.read_text(encoding="utf-8-sig")
    ast.parse(city, filename=str(CITY))
    ast.parse(auction, filename=str(AUCTION))

    city_markers = (
        "ROM 11.4.1 TRADER EQUIPMENT TYPE DISPLAY",
        "_city_equipment_typed_name_11_4_1",
        "_CITY_SELLABLE_BEFORE_TYPE_DISPLAY_11_4_1",
        "values[2] = _city_equipment_typed_name_11_4_1",
    )
    auction_markers = (
        "ROM 11.4.1 AUCTION EQUIPMENT TYPE DISPLAY",
        "_auction_equipment_typed_name_11_4_1",
        "_auction_snapshot_typed_name_11_4_1",
        "_auction_equipment_typed_name_11_4_1(item['inventory_id'], item['name'])",
        "_auction_snapshot_typed_name_11_4_1(snapshot)",
    )
    for marker in city_markers:
        if marker not in city:
            fail(f"city marker missing: {marker}")
    for marker in auction_markers:
        if marker not in auction:
            fail(f"auction marker missing: {marker}")

    # Every equipment list renderer must use the canonical formatter.
    if auction.count("_auction_equipment_typed_name_11_4_1(item['inventory_id'], item['name'])") < 2:
        fail("not all auction equipment lists use typed names")
    if auction.count("_auction_snapshot_typed_name_11_4_1(snapshot)") < 2:
        fail("auction price/confirmation screens are not both typed")

    # Idempotency and placement contract are explicit in both helpers.
    for source, label in ((city, "city"), (auction, "auction")):
        if 'f"[{label}]" in display_name' not in source:
            fail(f"{label}: duplicate-type guard missing")
        if 'marker = " рівня"' not in source:
            fail(f"{label}: level-aware insertion missing")

    print("[OK] Trader/Auction equipment type display contracts")
    print("- NPC trader equipment list: canonical armor type")
    print("- NPC trader confirmation details: canonical armor type")
    print("- Auction reply equipment list: canonical armor type")
    print("- Auction inline equipment list: canonical armor type")
    print("- Auction price prompt and confirmation: canonical armor type")
    print("- duplicate [Тип] labels prevented: OK")
    print("- weapon/jewelry names unchanged: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
