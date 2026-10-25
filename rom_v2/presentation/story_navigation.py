"""Framework-neutral Story navigation callback and presentation contract."""
from __future__ import annotations
from dataclasses import dataclass
PREFIX="sqh:v2";ROOT=f"{PREFIX}:index";PROFILE="story_quest:profile";MAX_CALLBACK_BYTES=64
@dataclass(frozen=True,slots=True)
class StoryRoute:
 surface:str;value:str|int|None=None
def encode_route(route:StoryRoute)->str:
 if route.surface=="index":value=ROOT
 elif route.surface in {"loc","sec","q"} and route.value is not None:value=f"{PREFIX}:{route.surface}:{route.value}"
 elif route.surface=="profile":value=PROFILE
 else:raise ValueError("invalid_story_route")
 if len(value.encode("utf-8"))>MAX_CALLBACK_BYTES:raise ValueError("story_callback_too_long")
 return value
def decode_route(data:str)->StoryRoute:
 if data==ROOT:return StoryRoute("index")
 if data==PROFILE:return StoryRoute("profile")
 parts=str(data).split(":",3)
 if len(parts)!=4 or parts[:2]!=["sqh","v2"] or parts[2] not in {"loc","sec","q"} or not parts[3]:raise ValueError("invalid_story_callback")
 return StoryRoute(parts[2],int(parts[3]) if parts[2]=="q" and parts[3].isdigit() else parts[3])
def parent_route(route:StoryRoute,quest_to_section:dict[int,str]|None=None,section_to_location:dict[str,str]|None=None)->StoryRoute:
 if route.surface=="q":
  if not quest_to_section or int(route.value) not in quest_to_section:raise KeyError("quest_parent_unknown")
  return StoryRoute("sec",quest_to_section[int(route.value)])
 if route.surface=="sec":
  if not section_to_location or str(route.value) not in section_to_location:raise KeyError("section_parent_unknown")
  return StoryRoute("loc",section_to_location[str(route.value)])
 if route.surface=="loc":return StoryRoute("index")
 if route.surface=="index":return StoryRoute("profile")
 raise ValueError("profile_has_no_story_parent")
