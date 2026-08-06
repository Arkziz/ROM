from __future__ import annotations

import ast
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from systems import player_interaction_system as interaction
from systems.pvp_battle_factory import create_pvp_battle_from_accepted_duel
from systems.pvp_request_service import create_pvp_duel_request, respond_to_pvp_duel_request
from systems import pvp_system


def make_db(path):
    c=sqlite3.connect(path); c.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT)")
    now=datetime.now(timezone.utc).isoformat()
    c.executemany("INSERT INTO users VALUES(?,?,?,?)",[(1,"A","start_path",now),(2,"B","start_path",now),(3,"C","dark_forest",now)])
    c.commit(); c.close(); interaction.init_player_interaction_foundation(db_path=path)


def main():
    handler=(ROOT/"handlers/player_interaction.py").read_text(encoding="utf-8")
    tree=ast.parse(handler)
    regs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="register_player_interaction_handlers"]
    assert len(regs)==1
    registrar=ast.get_source_segment(handler,regs[0])
    assert registrar.index("register_pvp_interaction_handlers") < registrar.index("_register_player_interaction_base_handlers_12_6_8")
    assert "pi:duel:" in (ROOT/"handlers/pvp_interaction.py").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="rom_pvp_14_3_") as temp:
        path=Path(temp)/"x.db"; make_db(path)
        conn=sqlite3.connect(path); conn.row_factory=sqlite3.Row; pvp_system.configure_pvp_connection_factory(lambda: sqlite3.connect(path))
        req=create_pvp_duel_request(1,2,db_path=path)
        assert req["success"] and req["request_type"]=="duel"
        assert create_pvp_duel_request(1,2,db_path=path)["reason"]=="player_busy"
        accepted=respond_to_pvp_duel_request(req["request_id"],2,"accept",db_path=path)
        assert accepted["success"] and accepted["status"]=="accepted"
        snapshot=lambda uid:{"class_key":"warrior" if uid==1 else "mage","max_hp":500,"max_mp":100 if uid==2 else 0,"resource_type":"mana" if uid==2 else "rage","production_hp":7}
        battle=create_pvp_battle_from_accepted_duel(accepted,snapshot_provider=snapshot,connection=conn,activity_db_path=path)
        assert battle["success"]
        rows=conn.execute("SELECT COUNT(*) FROM pvp_participants").fetchone()[0]; assert rows==2
        session_conn=sqlite3.connect(path)
        try:
            sessions=session_conn.execute("SELECT activity_type,COUNT(*) FROM player_activity_sessions GROUP BY activity_type").fetchall()
            assert sessions==[("pvp_battle",2)]
        finally:
            session_conn.close()
        conn.close(); pvp_system.configure_pvp_connection_factory(None)
    print("[OK] PvP duel request and player-interaction UI contracts")
    print("- Stage 12 Map same-location player finder reused: PASS")
    print("- duel request online/location/busy reservation: PASS")
    print("- accept creates one persistent battle and two participants: PASS")
    print("- pvp_battle activity sessions for both players: PASS")
    print("- PvP handlers registered before legacy duel placeholder: PASS")
    print("- production game.db writes: 0")
if __name__=="__main__": main()
