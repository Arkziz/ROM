"""Application service for audited HP/MP lifecycle transitions."""
from __future__ import annotations
from dataclasses import dataclass
from rom_v2.application.resource_ports import ResourceUnitOfWorkFactoryPort
from rom_v2.domain.resource_lifecycle import ResourceState,apply_pve_defeat,initialize_resources,restore_resources,set_current_resources,synchronize_maximums
@dataclass(frozen=True,slots=True)
class ResourceResult:
    status:str; reason:str; state:ResourceState|None
class ResourceService:
    def __init__(self,uow_factory:ResourceUnitOfWorkFactoryPort)->None:self._uow_factory=uow_factory
    def load(self,character_id:str,*,max_hp:int,max_mp:int)->ResourceResult:
        with self._uow_factory() as unit:
            state=unit.resources.get(character_id,max_hp,max_mp)
            return ResourceResult("found" if state else "not_found","ok" if state else "character_not_found",state)
    def initialize(self,character_id:str,class_key:str,*,max_hp:int,max_mp:int)->ResourceResult:
        state=initialize_resources(class_key,max_hp,max_mp)
        with self._uow_factory() as unit:unit.resources.save_current(character_id,state);unit.commit()
        return ResourceResult("updated","resource_initialized",state)
    def synchronize(self,character_id:str,class_key:str,*,old_max_hp:int,old_max_mp:int,new_max_hp:int,new_max_mp:int)->ResourceResult:
        with self._uow_factory() as unit:
            state=unit.resources.get(character_id,old_max_hp,old_max_mp)
            if state is None:return ResourceResult("not_found","character_not_found",None)
            updated=synchronize_maximums(state,class_key,new_max_hp,new_max_mp);unit.resources.save_current(character_id,updated);unit.commit()
        return ResourceResult("updated","resource_maximums_synchronized",updated)
    def set_current(self,character_id:str,*,max_hp:int,max_mp:int,current_hp:int|None=None,current_mp:int|None=None)->ResourceResult:
        with self._uow_factory() as unit:
            state=unit.resources.get(character_id,max_hp,max_mp)
            if state is None:return ResourceResult("not_found","character_not_found",None)
            updated=set_current_resources(state,current_hp=current_hp,current_mp=current_mp);unit.resources.save_current(character_id,updated);unit.commit()
        return ResourceResult("updated","current_resources_updated",updated)
    def restore(self,character_id:str,*,max_hp:int,max_mp:int,hp_amount:int=0,mp_amount:int=0)->ResourceResult:
        with self._uow_factory() as unit:
            state=unit.resources.get(character_id,max_hp,max_mp)
            if state is None:return ResourceResult("not_found","character_not_found",None)
            updated=restore_resources(state,hp_amount=hp_amount,mp_amount=mp_amount);unit.resources.save_current(character_id,updated);unit.commit()
        return ResourceResult("updated","resources_restored",updated)
    def defeat(self,character_id:str,*,max_hp:int,max_mp:int)->ResourceResult:
        with self._uow_factory() as unit:
            state=unit.resources.get(character_id,max_hp,max_mp)
            if state is None:return ResourceResult("not_found","character_not_found",None)
            updated=apply_pve_defeat(state);unit.resources.save_current(character_id,updated);unit.commit()
        return ResourceResult("updated","pve_defeat_applied",updated)
