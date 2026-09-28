#!/usr/bin/env python3
from __future__ import annotations
import inspect,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import handlers.story_quest_npc_runtime as runtime

def main():
 original=runtime.db.conn
 connection=sqlite3.connect(':memory:');connection.row_factory=sqlite3.Row
 connection.execute('CREATE TABLE users(user_id INTEGER PRIMARY KEY, level INTEGER)')
 connection.execute('INSERT INTO users(user_id,level) VALUES(101,7)');connection.commit()
 try:
  runtime.db.conn=connection
  assert runtime._player_level(101)==7
  assert runtime._player_level(999)==1
  source=inspect.getsource(runtime.has_story_npc_if_present)
  assert '_player_level(message.from_user.id)' in source
 finally:
  runtime.db.conn=original;connection.close()
 print('STORY NPC LEVEL PROBE: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
