"""Single canonical V2 rune lifecycle mutation service."""
from __future__ import annotations
from dataclasses import replace
from typing import Protocol
from rom_v2.domain.runes import (RuneDefinition,RuneEquipmentState,RuneFailure,
    RuneMutationResult,RuneSocket,RuneStatContribution)

class RuneLifecycleGateway(Protocol):
    """Atomic persistence boundary owned by infrastructure, not presentation."""
    def load_equipment(self,user_id:int,inventory_id:int)->RuneEquipmentState|None: ...
    def rune_quantity(self,user_id:int,rune_item_id:int)->int: ...
    def is_reserved(self,user_id:int,inventory_id:int)->bool: ...
    def extractor_quantity(self,user_id:int,item_id:int)->int: ...
    def gold(self,user_id:int)->int: ...
    def commit_insert(self,*,expected:RuneEquipmentState,updated:RuneEquipmentState,
                      rune_item_id:int)->bool: ...
    def commit_extract(self,*,expected:RuneEquipmentState,updated:RuneEquipmentState,
                       rune_item_id:int,extractor_item_id:int|None,gold_cost:int)->bool: ...

class RuneLifecycleService:
    """Validates V1-parity invariants before one atomic gateway mutation."""
    def __init__(self,gateway:RuneLifecycleGateway)->None:
        self._gateway=gateway

    def insert(self,*,user_id:int,equipment_inventory_id:int,slot_index:int,
               rune:RuneDefinition,character_class:str)->RuneMutationResult:
        equipment=self._owned_equipment(user_id,equipment_inventory_id)
        failure=self._insertion_failure(equipment,user_id,slot_index,rune,character_class)
        if failure is not None: return RuneMutationResult(False,failure)
        assert equipment is not None
        sockets=dict(equipment.sockets)
        sockets[slot_index]=RuneSocket(slot_index,rune,equipment_inventory_id)
        updated=replace(equipment,sockets=sockets)
        if not self._gateway.commit_insert(expected=equipment,updated=updated,rune_item_id=rune.item_id):
            return RuneMutationResult(False,RuneFailure.CONCURRENT_CHANGE)
        return RuneMutationResult(True,"inserted",updated)

    def extract(self,*,user_id:int,equipment_inventory_id:int,slot_index:int,
                extractor_item_id:int|None=None,gold_cost:int=0)->RuneMutationResult:
        equipment=self._owned_equipment(user_id,equipment_inventory_id)
        if equipment is None: return RuneMutationResult(False,RuneFailure.NOT_OWNED)
        if self._gateway.is_reserved(user_id,equipment_inventory_id):
            return RuneMutationResult(False,RuneFailure.RESERVED)
        socket=equipment.sockets.get(slot_index)
        if socket is None: return RuneMutationResult(False,RuneFailure.RUNE_NOT_FOUND)
        if gold_cost<0: return RuneMutationResult(False,RuneFailure.INSUFFICIENT_GOLD)
        if extractor_item_id is not None and self._gateway.extractor_quantity(user_id,extractor_item_id)<1:
            return RuneMutationResult(False,RuneFailure.NO_EXTRACTOR)
        if self._gateway.gold(user_id)<gold_cost:
            return RuneMutationResult(False,RuneFailure.INSUFFICIENT_GOLD)
        sockets=dict(equipment.sockets); del sockets[slot_index]
        updated=replace(equipment,sockets=sockets)
        if not self._gateway.commit_extract(expected=equipment,updated=updated,
                rune_item_id=socket.rune.item_id,extractor_item_id=extractor_item_id,gold_cost=gold_cost):
            return RuneMutationResult(False,RuneFailure.CONCURRENT_CHANGE)
        return RuneMutationResult(True,"extracted",updated,socket.rune.item_id,extractor_item_id,gold_cost)

    def contributions(self,equipment:RuneEquipmentState)->tuple[RuneStatContribution,...]:
        """Only equipped, non-broken items contribute; each socket applies once."""
        if not equipment.equipped or equipment.durability<=0: return ()
        return tuple(RuneStatContribution(s.rune.stat_key,s.rune.value,s.rune.item_id,
                    equipment.inventory_id,i) for i,s in sorted(equipment.sockets.items()))

    def _owned_equipment(self,user_id:int,inventory_id:int)->RuneEquipmentState|None:
        if user_id<=0 or inventory_id<=0: return None
        value=self._gateway.load_equipment(user_id,inventory_id)
        return value if value is not None and value.owner_user_id==user_id else None

    def _insertion_failure(self,equipment:RuneEquipmentState|None,user_id:int,slot_index:int,
                           rune:RuneDefinition,character_class:str)->str|None:
        if equipment is None: return RuneFailure.NOT_OWNED
        if self._gateway.is_reserved(user_id,equipment.inventory_id): return RuneFailure.RESERVED
        if slot_index<0 or slot_index>=equipment.socket_capacity: return RuneFailure.INVALID_SOCKET
        if slot_index in equipment.sockets: return RuneFailure.SOCKET_OCCUPIED
        if equipment.allowed_classes and character_class not in equipment.allowed_classes:
            return RuneFailure.INCOMPATIBLE_CLASS
        if rune.allowed_classes and character_class not in rune.allowed_classes:
            return RuneFailure.INCOMPATIBLE_CLASS
        if self._gateway.rune_quantity(user_id,rune.item_id)<1: return RuneFailure.NOT_OWNED
        return None
