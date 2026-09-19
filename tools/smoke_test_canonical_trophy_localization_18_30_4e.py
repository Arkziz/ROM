from __future__ import annotations
import json,sqlite3,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];db=R/"game.db";before=db.read_bytes();runner=R/"tools"/"run_class_progression_simulation.py";x=subprocess.run([sys.executable,str(runner),"--class","scout","--target-level","2","--seed","1","--max-days","30"],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr
data=json.loads((R/"reports"/"simulation"/"stage_18_30_progression_scout_level_1_to_2_seed_1.json").read_text(encoding="utf-8"));rows=[row for row in data["loot_lifecycle"] if 107<=int(row["item_id"])<=126];assert rows,"Expected canonical trophy drops"
con=sqlite3.connect(f"file:{db.resolve().as_posix()}?mode=ro",uri=True)
try:names={int(i):str(n) for i,n in con.execute("SELECT id,name FROM items WHERE id BETWEEN 107 AND 126").fetchall()}
finally:con.close()
assert names,"Canonical trophy catalog missing";assert all(row["name_uk"]==names[int(row["item_id"])] for row in rows);assert all(not row["name_uk"].startswith("Предмет ID") and row["name_uk"]!="Трофей моба" for row in rows);assert db.read_bytes()==before
print("[PASS] canonical trophy names resolved read-only from existing item catalog")
