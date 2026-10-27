"""Six-class deterministic simulator matrix without long-run execution.

This flat domain module coordinates short contract probes only. Character
creation, stats, equipment, runes, skills and combat remain owned by injected
production-domain adapters. No simulator-only formulas are defined here.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

class CharacterClass(str, Enum):
    WARRIOR="warrior"
    KNIGHT="knight"
    SCOUT="scout"
    ROGUE="rogue"
    MAGE="mage"
    PRIEST="priest"

SIX_CLASS_ORDER=tuple(CharacterClass)

class SixClassProbePort(Protocol):
    """Adapter boundary to existing production-domain behavior."""
    def create_character(self, class_key: str) -> Any: ...
    def stat_snapshot(self, character: Any) -> Mapping[str, Any]: ...
    def equipment_compatibility(self, character: Any) -> Mapping[str, Any]: ...
    def skill_loadout(self, character: Any) -> tuple[str, ...]: ...
    def encounter_setup(self, character: Any) -> Mapping[str, Any]: ...
    def controlled_turns(self, character: Any, *, maximum_turns: int) -> Mapping[str, Any]: ...

@dataclass(frozen=True,slots=True)
class ClassProbeResult:
    class_key:str
    character_created:bool
    stat_snapshot_ready:bool
    equipment_contract_ready:bool
    skill_loadout_ready:bool
    encounter_ready:bool
    controlled_turns_executed:int
    details:Mapping[str,Any]

@dataclass(frozen=True,slots=True)
class SixClassMatrixResult:
    results:tuple[ClassProbeResult,...]
    long_run_executed:bool=False
    @property
    def class_keys(self)->tuple[str,...]: return tuple(x.class_key for x in self.results)
    @property
    def complete(self)->bool:
        return self.class_keys==tuple(x.value for x in SIX_CLASS_ORDER) and all(
            x.character_created and x.stat_snapshot_ready and x.equipment_contract_ready
            and x.skill_loadout_ready and x.encounter_ready and 0 <= x.controlled_turns_executed <= 3
            for x in self.results
        )

class SixClassSimulationMatrix:
    """Runs six short deterministic probes; never a 1-to-10 progression run."""
    MAX_CONTROLLED_TURNS=3
    def __init__(self,port:SixClassProbePort)->None: self._port=port
    def run_contract_probes(self,*,maximum_turns:int=1)->SixClassMatrixResult:
        if isinstance(maximum_turns,bool) or not 0 <= maximum_turns <= self.MAX_CONTROLLED_TURNS:
            raise ValueError("maximum_turns_must_be_between_0_and_3")
        results=[]
        for cls in SIX_CLASS_ORDER:
            character=self._port.create_character(cls.value)
            if character is None: raise ValueError(f"character_creation_failed::{cls.value}")
            stats=self._port.stat_snapshot(character)
            equipment=self._port.equipment_compatibility(character)
            skills=tuple(self._port.skill_loadout(character))
            encounter=self._port.encounter_setup(character)
            turns=self._port.controlled_turns(character,maximum_turns=maximum_turns) if maximum_turns else {"turns_executed":0}
            executed=turns.get("turns_executed")
            if isinstance(executed,bool) or not isinstance(executed,int) or not 0 <= executed <= maximum_turns:
                raise ValueError(f"invalid_controlled_turn_count::{cls.value}")
            results.append(ClassProbeResult(
                class_key=cls.value,character_created=True,
                stat_snapshot_ready=bool(stats),equipment_contract_ready=bool(equipment),
                skill_loadout_ready=bool(skills),encounter_ready=bool(encounter),
                controlled_turns_executed=executed,
                details={"stats":stats,"equipment":equipment,"skills":skills,"encounter":encounter,"turns":turns},
            ))
        return SixClassMatrixResult(tuple(results),long_run_executed=False)
