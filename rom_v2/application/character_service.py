"""Application service for V1-faithful character creation and reset."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from rom_v2.application.character_ports import CharacterUnitOfWorkFactoryPort
from rom_v2.domain.character import Character,character_name_key,validate_character_name
from rom_v2.domain.class_catalog import ClassCatalog,DEFAULT_CLASS_CATALOG
class CharacterResultStatus(StrEnum):CREATED="created";RESET="reset";ALREADY_EXISTS="already_exists";REJECTED="rejected";NOT_FOUND="not_found"
@dataclass(frozen=True,slots=True)
class CreateCharacterCommand:
 character_id:str;account_id:str;name:str;class_key:str;location_key:str;current_hp:int;current_mp:int|None
@dataclass(frozen=True,slots=True)
class ResetCharacterCommand:character_id:str
@dataclass(frozen=True,slots=True)
class CharacterCommandResult:status:CharacterResultStatus;reason:str;character:Character|None
class CharacterService:
 """Own V1-parity creation and reset mutations through application ports."""
 def __init__(self,unit_of_work_factory:CharacterUnitOfWorkFactoryPort,class_catalog:ClassCatalog=DEFAULT_CLASS_CATALOG)->None:self._unit_of_work_factory=unit_of_work_factory;self._class_catalog=class_catalog
 def create(self,command:CreateCharacterCommand)->CharacterCommandResult:
  if self._class_catalog.find(command.class_key) is None:return CharacterCommandResult(CharacterResultStatus.REJECTED,"class_key_unknown",None)
  try:
   normalized=validate_character_name(command.name);candidate=Character(command.character_id,command.account_id,normalized,command.class_key,1,0,command.location_key,command.current_hp,command.current_mp)
  except ValueError as error:return CharacterCommandResult(CharacterResultStatus.REJECTED,str(error),None)
  with self._unit_of_work_factory() as unit:
   existing=unit.characters.find_by_account_id(candidate.account_id)
   if existing is not None:return CharacterCommandResult(CharacterResultStatus.ALREADY_EXISTS,"account_character_exists",existing)
   if unit.characters.find_by_id(candidate.character_id) is not None:return CharacterCommandResult(CharacterResultStatus.REJECTED,"character_id_exists",None)
   if unit.characters.find_by_name_key(character_name_key(candidate.name)) is not None:return CharacterCommandResult(CharacterResultStatus.REJECTED,"character_name_exists",None)
   unit.characters.add(candidate);unit.commit()
  return CharacterCommandResult(CharacterResultStatus.CREATED,"character_created",candidate)
 def reset(self,command:ResetCharacterCommand)->CharacterCommandResult:
  with self._unit_of_work_factory() as unit:
   current=unit.characters.find_by_id(command.character_id)
   if current is None:return CharacterCommandResult(CharacterResultStatus.NOT_FOUND,"character_not_found",None)
   # V1 DEV reset clears name and class; deleting the V2 character aggregate returns the account to registration.
   unit.characters.delete(command.character_id);unit.commit()
  return CharacterCommandResult(CharacterResultStatus.RESET,"character_reset_requires_registration",None)
