#!/usr/bin/env python3
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.story_quest_player_level import resolve_story_quest_player_level
from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_system import get_story_quest_view
assert resolve_story_quest_player_level({'level':2})==2
class MappingLike:
 def keys(self):return ['level']
 def __getitem__(self,key):return 2
assert resolve_story_quest_player_level(MappingLike())==2
class ObjectLevel:level='2'
assert resolve_story_quest_player_level(ObjectLevel())==2
assert resolve_story_quest_player_level({'level':0})==1
memory=sqlite3.connect(':memory:');memory.row_factory=sqlite3.Row
row=memory.execute('SELECT 2 AS level').fetchone();assert resolve_story_quest_player_level(row)==2;memory.close()
db=sqlite3.connect((ROOT/'game.db').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
try:
 user=db.execute("SELECT user_id,level FROM users WHERE character_name='Arkziz'").fetchone();assert user
 assert resolve_story_quest_player_level(user)==2
 q=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==11)
 view=get_story_quest_view(db,user_id=int(user['user_id']),quest=q,player_level=resolve_story_quest_player_level(user))
 assert view['status']=='AVAILABLE',view
finally:db.close()
print('STORY QUEST PLAYER LEVEL PROBE: PASS')
