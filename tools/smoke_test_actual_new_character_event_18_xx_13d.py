# -*- coding: utf-8 -*-
from __future__ import annotations
import sqlite3, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import systems.character_system as character
from systems.world_chronicle_system import init_world_chronicle_system

class DB:
    def __init__(self,path):
        self.conn=sqlite3.connect(path)
        self.cursor=self.conn.cursor()
    def close(self):self.conn.close()

with tempfile.TemporaryDirectory() as directory:
    database=Path(directory)/"runtime.db"
    connection=sqlite3.connect(database)
    connection.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY, character_name TEXT, character_class TEXT DEFAULT '', class_selected_at TEXT DEFAULT '')")
    connection.execute("INSERT INTO users(user_id,character_name,character_class,class_selected_at) VALUES(1,'Новий герой','','')")
    connection.execute("INSERT INTO users(user_id,character_name,character_class,class_selected_at) VALUES(2,'Чинний герой','mage','2026-09-16T20:00:00')")
    connection.commit();connection.close();init_world_chronicle_system(database)

    active=[]
    original_db=character._db;original_init=character.init_character_class_system;original_refresh=character.refresh_user_mp
    character._db=lambda: (active.append(DB(database)) or active[-1])
    character.init_character_class_system=lambda: None
    character.refresh_user_mp=lambda user_id: None
    try:
        result=character.confirm_initial_character_class_17_13_1(1,"warrior")
        assert result["success"] is True,result
        replay=character.confirm_initial_character_class_17_13_1(1,"knight")
        assert replay["success"] is False,replay
        existing=character.confirm_initial_character_class_17_13_1(2,"scout")
        assert existing["success"] is False,existing
    finally:
        character._db=original_db;character.init_character_class_system=original_init;character.refresh_user_mp=original_refresh
        for item in active:item.close()

    connection=sqlite3.connect(database)
    rows=connection.execute("SELECT event_type,actor_user_id,actor_name_snapshot,deduplication_key FROM world_chronicle_events ORDER BY id").fetchall()
    user=connection.execute("SELECT character_class,class_selected_at FROM users WHERE user_id=1").fetchone()
    connection.close()
    assert rows==[("player_joined",1,"Новий герой","player_joined:1")],rows
    assert user[0]=="warrior" and str(user[1] or "").strip(),user

source=(ROOT/"systems"/"character_system.py").read_text(encoding="utf-8-sig")
tree=__import__("ast").parse(source)
def segment(name):
    owners=[n for n in tree.body if isinstance(n,(__import__("ast").FunctionDef,__import__("ast").AsyncFunctionDef)) and n.name==name]
    assert len(owners)==1,(name,len(owners));return __import__("ast").get_source_segment(source,owners[0]) or ""
actual=segment("confirm_initial_character_class_17_13_1")
legacy=segment("set_character_class")
assert actual.count('"player_joined"')==1
assert "connection=db.conn" in actual
assert legacy.count('"player_joined"')==0
print("ACTUAL_NEW_CHARACTER_EVENT_18_XX_13D_OK")
