"""Application service for ROM V2 character creation and reset lifecycle."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from rom_v2.application.character_ports import CharacterUnitOfWorkFactoryPort
from rom_v2.domain.character import Character

class CharacterResultStatus(StrEnum):
    CREATED="created"; RESET="reset"; ALREADY_EXISTS="already_exists"; REJECTED="rejected"; NOT_FOUND="not_found"

@dataclass(frozen=True, slots=True)
class CreateCharacterCommand:
    character_id: str; account_id: str; name: str; class_key: str; location_key: str; current_hp: int; current_mp: int | None

@dataclass(frozen=True, slots=True)
class ResetCharacterCommand:
    character_id: str; expected_version: int; location_key: str; current_hp: int; current_mp: int | None

@dataclass(frozen=True, slots=True)
class CharacterCommandResult:
    status: CharacterResultStatus; reason: str; character: Character | None

class CharacterService:
    """Own character lifecycle mutations through application ports and one UoW."""
    def __init__(self, unit_of_work_factory: CharacterUnitOfWorkFactoryPort) -> None:
        self._unit_of_work_factory=unit_of_work_factory

    def create(self, command: CreateCharacterCommand) -> CharacterCommandResult:
        try:
            candidate=Character(command.character_id,command.account_id,command.name,command.class_key,1,0,command.location_key,command.current_hp,command.current_mp)
        except ValueError as error:
            return CharacterCommandResult(CharacterResultStatus.REJECTED,str(error),None)
        with self._unit_of_work_factory() as unit:
            existing=unit.characters.find_by_account_id(candidate.account_id)
            if existing is not None: return CharacterCommandResult(CharacterResultStatus.ALREADY_EXISTS,"account_character_exists",existing)
            if unit.characters.find_by_id(candidate.character_id) is not None: return CharacterCommandResult(CharacterResultStatus.REJECTED,"character_id_exists",None)
            if unit.characters.find_by_name(candidate.name) is not None: return CharacterCommandResult(CharacterResultStatus.REJECTED,"character_name_exists",None)
            unit.characters.add(candidate); unit.commit()
        return CharacterCommandResult(CharacterResultStatus.CREATED,"character_created",candidate)

    def reset(self, command: ResetCharacterCommand) -> CharacterCommandResult:
        with self._unit_of_work_factory() as unit:
            current=unit.characters.find_by_id(command.character_id)
            if current is None: return CharacterCommandResult(CharacterResultStatus.NOT_FOUND,"character_not_found",None)
            if current.version != command.expected_version: return CharacterCommandResult(CharacterResultStatus.REJECTED,"character_version_conflict",current)
            try: updated=current.reset(location_key=command.location_key,current_hp=command.current_hp,current_mp=command.current_mp)
            except ValueError as error: return CharacterCommandResult(CharacterResultStatus.REJECTED,str(error),current)
            unit.characters.reset(updated,expected_version=command.expected_version); unit.commit()
        return CharacterCommandResult(CharacterResultStatus.RESET,"character_reset",updated)
