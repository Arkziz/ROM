"""Pure guild contract completion and history DTOs."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class GuildContractCompletion:
 completion_key:str;user_id:int;target_name:str;actor_name:str|None=None
 def __post_init__(self):
  if not self.completion_key.strip():raise ValueError("missing_completion_key")
  if self.user_id<1:raise ValueError("invalid_user_id")
  if not self.target_name.strip():raise ValueError("missing_target_name")
@dataclass(frozen=True,slots=True)
class GuildHistoryEvent:
 event_id:int;guild_id:int;event_code:str;target_name:str;actor_name:str|None=None
@dataclass(frozen=True,slots=True)
class GuildHistoryPage:
 guild_id:int;items:tuple[GuildHistoryEvent,...];total:int;limit:int;offset:int

def completion_from_legacy(completion_key,user_id,payload,actor_name=None):
 if isinstance(payload,str):target=payload.strip()
 elif isinstance(payload,dict):target=next((str(payload.get(k) or "").strip() for k in ("target_mob_name","name","title","contract_name") if str(payload.get(k) or "").strip()),"")
 else:target=""
 return GuildContractCompletion(str(completion_key).strip(),int(user_id),target,actor_name)
