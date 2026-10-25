"""Atomic framework-neutral V2 overlevel reconciliation service."""
from __future__ import annotations
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass,field
from collections.abc import Iterable,Mapping
from rom_v2.domain.overlevel_policy import *

@dataclass
class InMemoryOverlevelUnitOfWork:
 rows:dict[int,dict[str,OverlevelQuestRow]]=field(default_factory=dict)
 quest_items:dict[int,dict[tuple[str,str],int]]=field(default_factory=dict)
 @contextmanager
 def atomic(self):
  snapshot=(deepcopy(self.rows),deepcopy(self.quest_items))
  try:yield self
  except Exception:
   self.rows,self.quest_items=snapshot;raise
 def user_rows(self,user_id:int):return self.rows.setdefault(int(user_id),{})
 def user_items(self,user_id:int):return self.quest_items.setdefault(int(user_id),{})

class OverlevelPolicyService:
 def __init__(self,uow:InMemoryOverlevelUnitOfWork,definitions:Iterable[OverlevelQuestDefinition],max_levels:Mapping[str,int]=LOCATION_MAX_LEVELS):
  ordered=tuple(sorted(definitions,key=lambda q:q.number))
  if not ordered or len({q.quest_id for q in ordered})!=len(ordered) or len({q.number for q in ordered})!=len(ordered):raise ValueError("invalid_overlevel_registry")
  self._uow=uow;self._definitions=ordered;self._max_levels=dict(max_levels)
  unknown={q.location_id for q in ordered}-set(self._max_levels)
  if unknown:raise ValueError("missing_location_max_level:"+repr(sorted(unknown)))
 def reconcile(self,user_id:int,current_level:int)->OverlevelReconciliationResult:
  user_id=int(user_id);current_level=int(current_level)
  if user_id<1 or current_level<1:raise ValueError("invalid_overlevel_request")
  exceeded=[loc for loc in self._max_levels if current_level>int(self._max_levels[loc])]
  results=[];changed=0
  with self._uow.atomic():
   rows=self._uow.user_rows(user_id);items=self._uow.user_items(user_id)
   for location_id in exceeded:
    defs=tuple(q for q in self._definitions if q.location_id==location_id)
    completed=already_skipped=skipped_now=0
    for definition in defs:
     row=rows.get(definition.quest_id)
     if row and row.status==OverlevelQuestStatus.COMPLETED:
      completed+=1;continue
     if row and row.status==OverlevelQuestStatus.SKIPPED:
      already_skipped+=1;continue
     progress=row.progress if row else 0
     rows[definition.quest_id]=OverlevelQuestRow(definition.quest_id,definition.number,location_id,OverlevelQuestStatus.SKIPPED,progress,definition.target_quantity,False)
     skipped_now+=1;changed+=1
    doomed=[key for key in items if key[0] in {q.quest_id for q in defs}]
    for key in doomed:del items[key]
    results.append(OverlevelLocationResult(location_id,int(self._max_levels[location_id]),completed,already_skipped,skipped_now,len(doomed)))
  return OverlevelReconciliationResult(current_level,changed,tuple(results))
