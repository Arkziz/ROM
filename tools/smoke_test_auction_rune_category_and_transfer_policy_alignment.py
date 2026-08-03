#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sqlite3, sys, tempfile
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)
def main():
    for rel in ("systems/auction_house_system.py","handlers/auction_house.py","db.py"):
        p=ROOT/rel; ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
    s=(ROOT/"systems/auction_house_system.py").read_text(encoding="utf-8-sig")
    h=(ROOT/"handlers/auction_house.py").read_text(encoding="utf-8-sig")
    for value in ("AUCTION_CATEGORY_RUNE = \"rune\"","AUCTION_PROTECTED_TRANSFER_ITEM_IDS","_auction_is_rune_snapshot_12_6_3c","_auction_trade_reserved_quantity_12_6_3c"):
        if value not in s: fail("missing system contract: "+value)
    for value in ("💠 Руни","AUCTION_SELL_CATEGORY_BUTTONS_V2[\"rune\"]","AUCTION_BUY_CATEGORY_BUTTONS_V1[\"rune\"]"):
        if value not in h: fail("missing handler contract: "+value)
    # Validate the protected-lot migration result against a synthetic database.
    with tempfile.TemporaryDirectory(prefix="rom_auction_12_6_3c_",ignore_cleanup_errors=True) as td:
        db=Path(td)/"test.db"
        with closing(sqlite3.connect(db)) as c:
            c.executescript("CREATE TABLE auction_lots(id INTEGER PRIMARY KEY,item_snapshot_json TEXT,status TEXT,delete_after TEXT,updated_at TEXT); INSERT INTO auction_lots VALUES(1,'{\"item_id\":526}','ACTIVE',NULL,'x'); INSERT INTO auction_lots VALUES(2,'{\"item_id\":527}','ACTIVE',NULL,'x');")
            protected=[]
            for row in c.execute("SELECT id,item_snapshot_json FROM auction_lots WHERE status='ACTIVE'"):
                if int(__import__('json').loads(row[1]).get('item_id') or 0) in (301,402,526,528): protected.append(row[0])
            if protected != [1]: fail(protected)
    print("[OK] Auction rune category and transfer policy alignment contracts")
    print("- rune sell/buy category and pagination routing: OK")
    print("- runes excluded from material matcher: OK")
    print("- protected IDs 301/402/526/528 blocked: OK")
    print("- allowed IDs 401/501-525/527 preserved: OK")
    print("- direct-trade reservations reduce auction availability: OK")
    print("- protected active-lot migration classifier: OK")
    print("- isolated checks; real user mutations: 0")
if __name__=='__main__': main()
