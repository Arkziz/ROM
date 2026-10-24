"""Pure guild application lifecycle model."""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import StrEnum
class ApplicationStatus(StrEnum):
 PENDING="pending"; ACCEPTED="accepted"; REJECTED="rejected"; CANCELLED="cancelled"
@dataclass(frozen=True,slots=True)
class GuildApplication:
 application_id:int; guild_id:int; user_id:int; status:ApplicationStatus=ApplicationStatus.PENDING; processed_by:int|None=None
 def __post_init__(self):
  if min(self.application_id,self.guild_id,self.user_id)<1: raise ValueError("invalid_application_identity")
  if self.status is ApplicationStatus.PENDING and self.processed_by is not None: raise ValueError("pending_has_processor")
  if self.status is not ApplicationStatus.PENDING and self.processed_by is None: raise ValueError("terminal_missing_processor")
 def decide(self,actor_id,status):
  if self.status is not ApplicationStatus.PENDING:return None,"already_processed"
  if status not in {ApplicationStatus.ACCEPTED,ApplicationStatus.REJECTED}:return None,"invalid_transition"
  return replace(self,status=status,processed_by=actor_id),None
