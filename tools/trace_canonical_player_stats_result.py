#!/usr/bin/env python3
from __future__ import annotations
import inspect,json,sqlite3,sys
from collections.abc import Mapping
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
CHARACTER="Arkziz"

def safe(fn):
 try:return {"ok":True,"value":fn()}
 except Exception as error:return {"ok":False,"error_type":type(error).__name__,"error":str(error)}
def source_info(fn):
 try:return {"module":fn.__module__,"qualname":fn.__qualname__,"signature":str(inspect.signature(fn)),"source_file":inspect.getsourcefile(fn),"source":inspect.getsource(fn)}
 except Exception as error:return {"error_type":type(error).__name__,"error":str(error)}
def shape(value):
 result={"type_module":type(value).__module__,"type_name":type(value).__qualname__,"repr":repr(value),"is_dict":isinstance(value,dict),"is_mapping":isinstance(value,Mapping),"is_tuple":isinstance(value,tuple),"is_list":isinstance(value,list),"has_keys":hasattr(value,"keys") and callable(getattr(value,"keys",None)),"has_level_attr":hasattr(value,"level")}
 result["len"]=safe(lambda:len(value));result["keys"]=safe(lambda:list(value.keys()));result["getitem_level"]=safe(lambda:value["level"]);result["attr_level"]=safe(lambda:getattr(value,"level"));result["index_5"]=safe(lambda:value[5]);result["sequence_values"]=list(value) if isinstance(value,(tuple,list)) else None
 return result

def main():
 from db import get_player_stats
 from systems.story_quest_player_level import resolve_story_quest_player_level
 from systems.story_quest_system import get_story_quest_view
 from data.story_quest_content import STORY_QUEST_REGISTRY
 db=sqlite3.connect((ROOT/'game.db').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  user=db.execute("SELECT user_id,character_name,level FROM users WHERE character_name=?",(CHARACTER,)).fetchone()
  if not user:raise RuntimeError('target character not found')
  user_id=int(user['user_id']);database_level=int(user['level'])
  stats=get_player_stats(user_id)
  adapter_level=resolve_story_quest_player_level(stats)
  legacy_positional_level=safe(lambda:int(stats[5] or 1))
  quest=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==11)
  adapter_view=get_story_quest_view(db,user_id=user_id,quest=quest,player_level=adapter_level)
  database_view=get_story_quest_view(db,user_id=user_id,quest=quest,player_level=database_level)
  positional_view=None
  if legacy_positional_level.get('ok'):
   positional_view=get_story_quest_view(db,user_id=user_id,quest=quest,player_level=legacy_positional_level['value'])
  result={
   "target":{"user_id":user_id,"character_name":user['character_name'],"database_level":database_level},
   "canonical_provider":{"source":source_info(get_player_stats),"result_shape":shape(stats)},
   "level_resolution":{"current_adapter_level":adapter_level,"legacy_positional_level":legacy_positional_level,"database_level":database_level},
   "quest_11":{"unlock_level":quest.unlock_level,"view_with_current_adapter":adapter_view['status'],"view_with_database_level":database_view['status'],"view_with_positional_level":None if positional_view is None else positional_view['status']},
  }
  if adapter_level!=database_level and legacy_positional_level.get('ok') and legacy_positional_level['value']==database_level:
   result['classification']='TUPLE_POSITIONAL_LEVEL_NOT_SUPPORTED_BY_ADAPTER';result['decision']='READY_FOR_STAGE_19_24_12_TUPLE_ADAPTER_FIX'
  elif adapter_level==database_level and adapter_view['status']=='AVAILABLE':
   result['classification']='CANONICAL_STATS_AND_ADAPTER_AVAILABLE_HANDLER_CLOSURE_PATH_SUSPECT';result['decision']='READY_FOR_STAGE_19_24_12_HANDLER_CLOSURE_TRACE'
  else:
   result['classification']='CANONICAL_STATS_CONTRACT_REQUIRES_TARGETED_REVIEW';result['decision']='READY_FOR_STAGE_19_24_12_TARGETED_FIX_PLANNING'
  print(json.dumps(result,ensure_ascii=False,indent=2,default=str));return 0
 finally:db.close()
if __name__=='__main__':raise SystemExit(main())
