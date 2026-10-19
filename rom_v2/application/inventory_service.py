"""V1-parity inventory orchestration: stacks, capacity and exact identity."""
from __future__ import annotations
from dataclasses import dataclass
from rom_v2.application.inventory_ports import InventoryReservationReaderPort, InventoryUnitOfWorkFactoryPort
from rom_v2.domain.item import ItemInstance

@dataclass(frozen=True,slots=True)
class InventoryResult:
    status:str
    reason:str|None=None
    instances:tuple[ItemInstance,...]=()
    affected_quantity:int=0

class InventoryService:
    def __init__(self,uow_factory:InventoryUnitOfWorkFactoryPort,reservations:InventoryReservationReaderPort|None=None):
        self._uow_factory=uow_factory; self._reservations=reservations

    def list_inventory(self,owner_user_id:int)->InventoryResult:
        with self._uow_factory() as uow:
            instances=tuple(uow.inventory.list_by_owner(owner_user_id))
            # The canonical UoW starts a transaction for every operation. End the
            # read-only transaction explicitly so a reused connection cannot retain
            # an open transaction before the next inventory command.
            uow.rollback()
            return InventoryResult("ok",instances=instances)

    def add_item(self,owner_user_id:int,item_id:int,quantity:int,capacity:int,max_stack:int)->InventoryResult:
        if min(owner_user_id,item_id,quantity,capacity,max_stack)<=0: return InventoryResult("rejected","invalid_inventory_request")
        with self._uow_factory() as uow:
            definition=uow.inventory.get_definition(item_id)
            if definition is None: return InventoryResult("rejected","item_definition_not_found")
            rows=list(uow.inventory.list_by_owner(owner_user_id)); same=[x for x in rows if x.item_id==item_id and x.quantity<max_stack]
            free=sum(max_stack-x.quantity for x in same); remaining=max(0,quantity-free); new_rows=(remaining+max_stack-1)//max_stack
            if len(rows)+new_rows>capacity: return InventoryResult("rejected","inventory_capacity_exceeded")
            left=quantity; changed=[]
            for row in same:
                transfer=min(left,max_stack-row.quantity)
                if transfer:
                    uow.inventory.change_quantity(row.inventory_id,row.quantity+transfer); changed.append(row.with_quantity(row.quantity+transfer)); left-=transfer
                if not left: break
            while left:
                transfer=min(left,max_stack); changed.append(uow.inventory.insert_instance(owner_user_id,item_id,transfer)); left-=transfer
            uow.commit(); return InventoryResult("ok",instances=tuple(changed),affected_quantity=quantity)

    def consume_exact(self,owner_user_id:int,inventory_id:int,quantity:int)->InventoryResult:
        if min(owner_user_id,inventory_id,quantity)<=0: return InventoryResult("rejected","invalid_inventory_request")
        with self._uow_factory() as uow:
            row=uow.inventory.get_instance(owner_user_id,inventory_id)
            if row is None: return InventoryResult("rejected","inventory_instance_not_found")
            reserved=self._reservations.reserved_quantity(owner_user_id,inventory_id) if self._reservations else 0
            if row.quantity-reserved<quantity: return InventoryResult("rejected","insufficient_available_quantity")
            remaining=row.quantity-quantity
            if remaining: uow.inventory.change_quantity(inventory_id,remaining)
            else: uow.inventory.delete_instance(inventory_id)
            uow.commit(); return InventoryResult("ok",affected_quantity=quantity)

    def consume_by_definition(self,owner_user_id:int,item_id:int,quantity:int)->InventoryResult:
        if min(owner_user_id,item_id,quantity)<=0: return InventoryResult("rejected","invalid_inventory_request")
        with self._uow_factory() as uow:
            rows=sorted((x for x in uow.inventory.list_by_owner(owner_user_id) if x.item_id==item_id),key=lambda x:x.inventory_id)
            available=[]; total=0
            for row in rows:
                reserved=self._reservations.reserved_quantity(owner_user_id,row.inventory_id) if self._reservations else 0
                amount=max(0,row.quantity-reserved); available.append((row,amount)); total+=amount
            if total<quantity: return InventoryResult("rejected","insufficient_available_quantity")
            left=quantity
            for row,amount in available:
                take=min(left,amount)
                if take:
                    remaining=row.quantity-take
                    if remaining: uow.inventory.change_quantity(row.inventory_id,remaining)
                    else: uow.inventory.delete_instance(row.inventory_id)
                    left-=take
                if not left: break
            uow.commit(); return InventoryResult("ok",affected_quantity=quantity)
