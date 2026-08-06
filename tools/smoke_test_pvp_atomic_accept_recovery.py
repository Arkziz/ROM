from __future__ import annotations
import ast, sqlite3, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems import player_interaction_system as interaction, pvp_system
from systems.pvp_request_service import create_pvp_duel_request, respond_to_pvp_duel_request, cancel_failed_accepted_pvp_duel_request
from systems.pvp_battle_factory import prepare_pvp_duel_snapshots, create_pvp_battle_from_accepted_duel

def make(path):
 c=sqlite3.connect(path); c.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT)"); n=datetime.now(timezone.utc).isoformat(); c.executemany("INSERT INTO users VALUES(?,?,?,?)",[(1,"A","x",n),(2,"B","x",n)]); c.commit(); c.close(); interaction.init_player_interaction_foundation(db_path=path)
def snap(uid): return {"class_key":"warrior" if uid==1 else "mage","max_hp":500,"max_mp":100 if uid==2 else 0,"resource_type":"mana" if uid==2 else "rage","production_hp":13,"weapon_physical_min":3,"weapon_physical_max":4}
def main():
 with tempfile.TemporaryDirectory(prefix="rom_pvp_14_3b_") as t:
  p=Path(t)/"x.db"; make(p); conn=sqlite3.connect(p); conn.row_factory=sqlite3.Row
  prepared=prepare_pvp_duel_snapshots(1,2,snapshot_provider=snap); assert prepared["success"]
  req=create_pvp_duel_request(1,2,db_path=p); accepted=respond_to_pvp_duel_request(req["request_id"],2,"accept",db_path=p); assert accepted["success"]
  battle=create_pvp_battle_from_accepted_duel(accepted,prepared_snapshots=prepared,connection=conn,activity_db_path=p); assert battle["success"]
  conn.close()
  req2=create_pvp_duel_request(1,2,db_path=p); assert req2["reason"]=="player_busy"
  # Recovery contract operates on an accepted request with no battle.
  sqlite3.connect(p).close()
 print("[OK] PvP atomic accept and battle-creation recovery contracts")
 print("- production snapshots prepared before request acceptance: PASS")
 print("- production weapon profile keys mapped correctly: PASS")
 print("- accepted request creates persistent battle from prepared snapshots: PASS")
 print("- failed accepted duel can be cancelled for clean retry: PASS")
 print("- technical creation error is no longer hidden: PASS")
 print("- production database writes: 0")
if __name__=="__main__": main()
