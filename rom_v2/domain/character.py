"""V1-faithful character aggregate and name policy for ROM V2."""
from __future__ import annotations
import re,unicodedata
from dataclasses import dataclass
NAME_MIN_LENGTH=2;NAME_MAX_LENGTH=24
FORBIDDEN_NON_UKRAINIAN_CYRILLIC_LETTERS=frozenset("ёЁъЪыЫэЭ")
def normalize_character_name(name:object)->str:
 """Match V1: strip, NFC-normalize, and collapse whitespace runs."""
 value=unicodedata.normalize("NFC",str(name or "").strip());return re.sub(r"\s+"," ",value)
def validate_character_name(name:object)->str:
 """Return the normalized V1-valid name or raise a machine-readable error."""
 value=normalize_character_name(name)
 if len(value)<NAME_MIN_LENGTH:raise ValueError("character_name_too_short")
 if len(value)>NAME_MAX_LENGTH:raise ValueError("character_name_too_long")
 if any(ch in FORBIDDEN_NON_UKRAINIAN_CYRILLIC_LETTERS for ch in value):raise ValueError("character_name_forbidden_letters")
 if not any(ch.isalpha() for ch in value):raise ValueError("character_name_letter_required")
 return value
def character_name_key(name:object)->str:return normalize_character_name(name).casefold()
@dataclass(frozen=True,slots=True)
class Character:
 character_id:str;account_id:str;name:str;class_key:str;level:int;experience:int;location_key:str;current_hp:int;current_mp:int|None
 def __post_init__(self)->None:
  if not self.character_id.strip():raise ValueError("character_id_required")
  if not self.account_id.strip():raise ValueError("account_id_required")
  normalized=validate_character_name(self.name)
  if normalized!=self.name:raise ValueError("character_name_not_normalized")
  if not self.class_key.strip():raise ValueError("class_key_required")
  if self.level<1:raise ValueError("character_level_invalid")
  if self.experience<0:raise ValueError("character_experience_invalid")
  if not self.location_key.strip():raise ValueError("location_key_required")
  if self.current_hp<0:raise ValueError("current_hp_invalid")
  if self.current_mp is not None and self.current_mp<0:raise ValueError("current_mp_invalid")
