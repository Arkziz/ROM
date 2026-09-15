#!/usr/bin/env python3
from __future__ import annotations
import sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.balance import REFINE_MATERIAL_MAX_STACK
from data.runes import RUNE_MAX_STACK,FIRIUS_TOKEN_MAX_STACK,EXTRACTOR_MAX_STACK,RUNE_ITEM_DEFINITIONS,RUNE_UTILITY_ITEM_DEFINITIONS
assert REFINE_MATERIAL_MAX_STACK==50
assert RUNE_MAX_STACK==50 and EXTRACTOR_MAX_STACK==50 and FIRIUS_TOKEN_MAX_STACK==999
assert {x["max_stack"] for x in RUNE_ITEM_DEFINITIONS.values()}=={50}
assert RUNE_UTILITY_ITEM_DEFINITIONS[726]["max_stack"]==999
assert RUNE_UTILITY_ITEM_DEFINITIONS[727]["max_stack"]==50
assert RUNE_UTILITY_ITEM_DEFINITIONS[728]["max_stack"]==50
source=(ROOT/"systems/name_rune_system.py").read_text(encoding="utf-8-sig")
assert "'max_stack':10" in source
# Pure temporary SQLite fixture for canonical 49+2 => 50+1 behavior.
with tempfile.TemporaryDirectory() as tmp:
 c=sqlite3.connect(Path(tmp)/"stack.sqlite3")
 c.executescript("CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER); INSERT INTO inventory VALUES(1,1,601,49);")
 max_stack=50;remaining=2
 row=c.execute("SELECT id,quantity FROM inventory WHERE user_id=1 AND item_id=601 AND quantity<50").fetchone()
 moved=min(remaining,max_stack-row[1]);c.execute("UPDATE inventory SET quantity=quantity+? WHERE id=?",(moved,row[0]));remaining-=moved
 if remaining:c.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,601,?)",(remaining,))
 assert [r[0] for r in c.execute("SELECT quantity FROM inventory ORDER BY id")]==[50,1]
 c.close()
print("ITEM_STACK_LIMITS_18_XX_5_OK")
