"""Application service for atomic V1-parity attribute allocation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from rom_v2.application.primary_stat_ports import PrimaryStatUnitOfWorkFactoryPort
from rom_v2.domain.primary_stats import AttributePointState,PrimaryStats,earned_points_for_level
class PrimaryStatResultStatus(StrEnum):UPDATED="updated";CREATED="created";REJECTED="rejected";NOT_FOUND="not_found"
@dataclass(frozen=True,slots=True)
class AllocatePrimaryStatsCommand:character_id:str;allocation:dict[str,int];expected_free_points:int
@dataclass(frozen=True,slots=True)
class PrimaryStatResult:status:PrimaryStatResultStatus;reason:str;state:AttributePointState|None
class PrimaryStatService:
 def __init__(self,uow_factory:PrimaryStatUnitOfWorkFactoryPort)->None:self._uow_factory=uow_factory
 def initialize(self,character_id:str,level:int=1)->PrimaryStatResult:
  earned=earned_points_for_level(level);state=AttributePointState(PrimaryStats(),earned,earned)
  with self._uow_factory() as unit:
   existing=unit.primary_stats.find(character_id)
   if existing is not None:return PrimaryStatResult(PrimaryStatResultStatus.UPDATED,"primary_stats_exist",existing)
   unit.primary_stats.add(character_id,state);unit.commit()
  return PrimaryStatResult(PrimaryStatResultStatus.CREATED,"primary_stats_created",state)
 def allocate(self,command:AllocatePrimaryStatsCommand)->PrimaryStatResult:
  with self._uow_factory() as unit:
   state=unit.primary_stats.find(command.character_id)
   if state is None:return PrimaryStatResult(PrimaryStatResultStatus.NOT_FOUND,"primary_stats_not_found",None)
   try:updated=state.allocate(command.allocation,command.expected_free_points)
   except ValueError as error:return PrimaryStatResult(PrimaryStatResultStatus.REJECTED,str(error),state)
   unit.primary_stats.replace(command.character_id,updated,command.expected_free_points);unit.commit()
  return PrimaryStatResult(PrimaryStatResultStatus.UPDATED,"primary_stats_allocated",updated)
 def respec(self,character_id:str,expected_free_points:int)->PrimaryStatResult:
  with self._uow_factory() as unit:
   state=unit.primary_stats.find(character_id)
   if state is None:return PrimaryStatResult(PrimaryStatResultStatus.NOT_FOUND,"primary_stats_not_found",None)
   if state.free_points!=expected_free_points:return PrimaryStatResult(PrimaryStatResultStatus.REJECTED,"attribute_state_stale",state)
   updated=state.respec();unit.primary_stats.replace(character_id,updated,expected_free_points);unit.commit()
  return PrimaryStatResult(PrimaryStatResultStatus.UPDATED,"primary_stats_respecced",updated)
