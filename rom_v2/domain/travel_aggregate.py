from __future__ import annotations
from dataclasses import dataclass,replace
from datetime import datetime
from enum import StrEnum
class TravelStatus(StrEnum):ACTIVE="active";ARRIVED="arrived";CANCELLED="cancelled";FAILED="failed"
@dataclass(frozen=True,slots=True)
class TravelAggregate:
 travel_id:int;user_id:int;from_node:str;to_node:str;status:TravelStatus;revision:int;started_at:datetime;arrival_at:datetime;cancelled_at:datetime|None=None;completed_at:datetime|None=None
 def __post_init__(self):
  if min(self.travel_id,self.user_id,self.revision)<1:raise ValueError("positive identity/revision required")
  if not self.from_node or not self.to_node or self.from_node==self.to_node:raise ValueError("distinct nodes required")
  if self.started_at.tzinfo is None or self.arrival_at.tzinfo is None or self.arrival_at<=self.started_at:raise ValueError("valid aware timeline required")
 def cancel(self,user_id,expected_revision,now):
  if user_id!=self.user_id:return None,"wrong_owner"
  if self.status is not TravelStatus.ACTIVE:return None,"already_terminal"
  if expected_revision!=self.revision:return None,"stale_revision"
  if now>=self.arrival_at:return None,"already_due"
  return replace(self,status=TravelStatus.CANCELLED,revision=self.revision+1,cancelled_at=now),None
 def complete(self,current_location,now):
  if self.status is not TravelStatus.ACTIVE:return None,"already_terminal"
  if now<self.arrival_at:return None,"not_due"
  if current_location!=self.from_node:return replace(self,status=TravelStatus.FAILED,revision=self.revision+1,completed_at=now),"source_changed"
  return replace(self,status=TravelStatus.ARRIVED,revision=self.revision+1,completed_at=now),None
