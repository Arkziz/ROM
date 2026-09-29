#!/usr/bin/env python3
from __future__ import annotations
import dataclasses
import inspect
import json
import sqlite3
import sys
from collections.abc import Mapping
from enum import Enum
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
TARGET_CHARACTER="Arkziz"
TARGET_NUMBER=11

def norm(value):
 if dataclasses.is_dataclass(value):
  return {field.name:norm(getattr(value,field.name)) for field in dataclasses.fields(value)}
 if isinstance(value,Enum):return value.value
 if isinstance(value,sqlite3.Row):return {key:norm(value[key]) for key in value.keys()}
 if isinstance(value,Mapping):return {str(key):norm(item) for key,item in value.items()}
 if isinstance(value,(tuple,list,set,frozenset)):return [norm(item) for item in value]
 if value is None or isinstance(value,(str,int,float,bool)):return value
 return repr(value)

def status_value(value):
 normalized=norm(value)
 if isinstance(normalized,dict):
  for key in ("status","derived_status","quest_status"):
   if key in normalized:return normalized[key]
 return normalized

def safe_source(obj):
 try:return {"name":getattr(obj,"__name__",repr(obj)),"signature":str(inspect.signature(obj)),"source":inspect.getsource(obj)}
 except Exception as error:return {"name":getattr(obj,"__name__",repr(obj)),"error":str(error)}

def main():
 from data.story_quest_content import STORY_QUEST_REGISTRY
 from data.story_quest_definitions import derive_story_quest_status
 from systems import story_quest_system as system
 from handlers import story_quests as journal
 from handlers import story_quest_npc_runtime as npc_runtime

 db_uri=(ROOT/'game.db').resolve().as_uri()+'?mode=ro'
 connection=sqlite3.connect(db_uri,uri=True)
 connection.row_factory=sqlite3.Row
 try:
  user=connection.execute("SELECT user_id,character_name,level FROM users WHERE character_name=?",(TARGET_CHARACTER,)).fetchone()
  if not user:raise RuntimeError(f"target character not found: {TARGET_CHARACTER}")
  user_id=int(user["user_id"]);player_level=int(user["level"] or 0)
  by_number={quest.number:quest for quest in STORY_QUEST_REGISTRY.values()}
  quest=by_number[TARGET_NUMBER];previous=STORY_QUEST_REGISTRY[quest.previous_quest_id]

  get_persisted=getattr(system,"get_story_quest")
  get_active=getattr(system,"get_active_story_quest")
  get_view=getattr(system,"get_story_quest_view")
  persistent=get_persisted(connection,user_id,quest.quest_id)
  predecessor=get_persisted(connection,user_id,quest.previous_quest_id)
  active=get_active(connection,user_id)
  predecessor_status=None if predecessor is None else predecessor["status"]
  predecessor_completed=bool(predecessor and predecessor_status in ("COMPLETED","SKIPPED"))
  another_active=active is not None
  pure=derive_story_quest_status(
   persistent_status=None if persistent is None else persistent["status"],
   player_level=player_level,
   unlock_level=quest.unlock_level,
   predecessor_completed=predecessor_completed,
   another_active_quest=another_active,
  )
  view=get_view(connection,user_id=user_id,quest=quest,player_level=player_level)

  journal_functions={name:safe_source(obj) for name,obj in vars(journal).items() if callable(obj) and ("quest" in name.lower() or "journal" in name.lower())}
  npc_functions={name:safe_source(obj) for name,obj in vars(npc_runtime).items() if callable(obj) and ("quest" in name.lower() or "npc" in name.lower() or "story" in name.lower())}
  system_functions={name:safe_source(obj) for name,obj in vars(system).items() if callable(obj) and name in ("get_story_quest_view","get_story_quest","get_active_story_quest","get_story_quest_journal")}

  result={
   "target":{"user_id":user_id,"character_name":user["character_name"],"player_level":player_level},
   "quest":{"quest_id":quest.quest_id,"number":quest.number,"unlock_level":quest.unlock_level,"previous_quest_id":quest.previous_quest_id,"giver_npc_id":quest.giver_npc_id},
   "predecessor_definition":{"quest_id":previous.quest_id,"number":previous.number},
   "runtime_inputs":{
    "persistent_quest_11":norm(persistent),
    "predecessor_row":norm(predecessor),
    "predecessor_raw_status":predecessor_status,
    "predecessor_completed":predecessor_completed,
    "active_story_quest":norm(active),
    "another_active_quest":another_active,
   },
   "pure_derived_status":status_value(pure),
   "production_view":norm(view),
   "production_view_status":status_value(view),
   "source_trace":{"system":system_functions,"journal":journal_functions,"npc_runtime":npc_functions},
  }
  expected="AVAILABLE"
  actual=result["production_view_status"]
  result["classification"]=("RESOLVER_RETURNS_AVAILABLE_PRESENTATION_PATH_SUSPECT" if actual==expected else "RESOLVER_RETURNS_NON_AVAILABLE_LIFECYCLE_PATH_SUSPECT")
  result["expected_status"]=expected
  print(json.dumps(result,ensure_ascii=False,indent=2))
  return 0
 finally:
  connection.close()

if __name__=="__main__":raise SystemExit(main())
