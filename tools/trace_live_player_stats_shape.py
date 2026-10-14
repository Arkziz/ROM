#!/usr/bin/env python3
from __future__ import annotations
import inspect,json,sqlite3,sys
from collections.abc import Mapping
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
CHARACTER="Arkziz"

def safe(call):
 try:return {"ok":True,"value":call()}
 except Exception as error:return {"ok":False,"error_type":type(error).__name__,"error":str(error)}
def shape(value):
 result={"type_module":type(value).__module__,"type_name":type(value).__qualname__,"is_dict":isinstance(value,dict),"is_mapping":isinstance(value,Mapping),"has_keys":hasattr(value,"keys") and callable(getattr(value,"keys",None)),"has_level_attr":hasattr(value,"level"),"repr":repr(value)}
 result["len"]=safe(lambda:len(value))
 result["keys"]=safe(lambda:list(value.keys()))
 result["getitem_level"]=safe(lambda:value["level"])
 result["get_level"]=safe(lambda:value.get("level"))
 result["attr_level"]=safe(lambda:getattr(value,"level"))
 if isinstance(value,(tuple,list)):
  result["sequence_values"]=list(value)
 return result

def source_info(obj):
 try:return {"module":obj.__module__,"name":obj.__name__,"signature":str(inspect.signature(obj)),"source_file":inspect.getsourcefile(obj),"source":inspect.getsource(obj)}
 except Exception as error:return {"error_type":type(error).__name__,"error":str(error)}

def main():
 from handlers import story_quests as journal
 from handlers import story_quest_npc_runtime as npc
 from systems.story_quest_player_level import resolve_story_quest_player_level
 from systems.story_quest_system import get_story_quest_view
 from data.story_quest_content import STORY_QUEST_REGISTRY
 # Resolve the actual provider used by each module. The handler may import a
 # module/alias rather than exposing get_player_stats as a module attribute.
 def resolve_provider(module):
  direct=getattr(module,"get_player_stats",None)
  if callable(direct):return direct,"module_attribute"
  source=inspect.getsource(module)
  candidates=[]
  for name,value in vars(module).items():
   if inspect.ismodule(value):
    fn=getattr(value,"get_player_stats",None)
    if callable(fn) and (name in source or getattr(value,"__name__","") in source):candidates.append((fn,f"module_alias:{name}"))
   elif callable(value) and getattr(value,"__name__","")=="get_player_stats":candidates.append((value,f"callable_alias:{name}"))
  unique=[]
  seen=set()
  for fn,origin in candidates:
   key=(getattr(fn,"__module__",None),getattr(fn,"__qualname__",None))
   if key not in seen:seen.add(key);unique.append((fn,origin))
  if len(unique)==1:return unique[0]
  return None,{"candidate_count":len(unique),"candidates":[{"origin":origin,"source":source_info(fn)} for fn,origin in unique]}
 journal_get,journal_origin=resolve_provider(journal)
 npc_get,npc_origin=resolve_provider(npc)
 if journal_get is None or npc_get is None:
  print(json.dumps({"classification":"PLAYER_STATS_PROVIDER_NOT_EXPOSED","journal_resolution":journal_origin,"npc_resolution":npc_origin,"journal_module_source":inspect.getsource(journal),"npc_module_source":inspect.getsource(npc)},ensure_ascii=False,indent=2));return 0
 db=sqlite3.connect((ROOT/'game.db').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  user=db.execute("SELECT user_id,character_name,level FROM users WHERE character_name=?",(CHARACTER,)).fetchone()
  if not user:raise RuntimeError('target character not found')
  user_id=int(user['user_id']);db_level=int(user['level'])
  journal_stats=journal_get(user_id);npc_stats=npc_get(user_id)
  journal_level=resolve_story_quest_player_level(journal_stats);npc_level=resolve_story_quest_player_level(npc_stats)
  quest=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==11)
  journal_view=get_story_quest_view(db,user_id=user_id,quest=quest,player_level=journal_level)
  npc_view=get_story_quest_view(db,user_id=user_id,quest=quest,player_level=npc_level)
  result={
   "target":{"user_id":user_id,"character_name":user['character_name'],"database_level":db_level},
   "journal_get_player_stats":{"resolution_origin":journal_origin,"identity_same_as_npc":journal_get is npc_get,"call_result_shape":shape(journal_stats),"adapter_level":journal_level,"source":source_info(journal_get)},
   "npc_get_player_stats":{"resolution_origin":npc_origin,"call_result_shape":shape(npc_stats),"adapter_level":npc_level,"source":source_info(npc_get)},
   "quest_11":{"unlock_level":quest.unlock_level,"journal_view_status":journal_view['status'],"npc_view_status":npc_view['status']},
   "journal_module_level_references":[line.strip() for line in inspect.getsource(journal).splitlines() if 'level' in line.lower() and ('stats' in line.lower() or 'resolve_story_quest_player_level' in line)],
   "npc_module_level_references":[line.strip() for line in inspect.getsource(npc).splitlines() if 'level' in line.lower() and ('stats' in line.lower() or 'resolve_story_quest_player_level' in line)],
  }
  if journal_level!=db_level or npc_level!=db_level:
   result['classification']='LIVE_STATS_SHAPE_NOT_SUPPORTED_BY_ADAPTER'
  elif journal_view['status']!='AVAILABLE' or npc_view['status']!='AVAILABLE':
   result['classification']='PRESENTATION_USES_DIFFERENT_RESOLVER_INPUT'
  else:
   result['classification']='LIVE_STATS_AND_DIRECT_VIEWS_AVAILABLE_HANDLER_RENDER_PATH_SUSPECT'
  print(json.dumps(result,ensure_ascii=False,indent=2,default=str));return 0
 finally:db.close()
if __name__=='__main__':raise SystemExit(main())
