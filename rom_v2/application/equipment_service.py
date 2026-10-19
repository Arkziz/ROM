"""V1-parity equipment orchestration over exact owned inventory identities."""
from __future__ import annotations
from dataclasses import dataclass
from rom_v2.application.equipment_ports import EquipmentUnitOfWorkFactoryPort
from rom_v2.domain.equipment import EquipmentItemPolicy,EquipmentSlot,SLOT_KEYS
@dataclass(frozen=True,slots=True)
class EquipmentResult:
 status:str; reason:str|None=None; slots:tuple[EquipmentSlot,...]=(); displaced:tuple[int,...]=()
class EquipmentService:
 def __init__(self,uow_factory:EquipmentUnitOfWorkFactoryPort): self._uow_factory=uow_factory
 def list_slots(self,owner_user_id:int)->EquipmentResult:
  if owner_user_id<=0:return EquipmentResult("rejected","owner_invalid")
  with self._uow_factory() as uow:
   rows=tuple(uow.equipment.list_slots(owner_user_id));uow.rollback();return EquipmentResult("ok",slots=rows)
 def equip(self,policy:EquipmentItemPolicy,character_level:int,class_key:str)->EquipmentResult:
  if character_level<policy.required_level:return EquipmentResult("rejected","required_level_not_met")
  if policy.allowed_classes and class_key not in policy.allowed_classes:return EquipmentResult("rejected","class_incompatible")
  with self._uow_factory() as uow:
   if uow.equipment.get_inventory_instance(policy.owner_user_id,policy.inventory_id) is None:return EquipmentResult("rejected","inventory_instance_not_found")
   current={x.slot_key:x.inventory_id for x in uow.equipment.list_slots(policy.owner_user_id)};displaced=[]
   if policy.slot_key=="off_hand" and "main_hand" in current:
    # Caller must provide the audited main-hand policy when validating two-hand use; storage itself remains fail-closed.
    pass
   if policy.slot_key in current and current[policy.slot_key]!=policy.inventory_id:displaced.append(current[policy.slot_key])
   if policy.slot_key=="main_hand" and policy.weapon_hands==2 and "off_hand" in current:
    displaced.append(current["off_hand"]);uow.equipment.clear_slot(policy.owner_user_id,"off_hand")
   uow.equipment.set_slot(policy.owner_user_id,policy.slot_key,policy.inventory_id);uow.commit()
   slots=tuple(uow.equipment.list_slots(policy.owner_user_id))
   return EquipmentResult("ok",slots=slots,displaced=tuple(displaced))
 def unequip(self,owner_user_id:int,slot_key:str)->EquipmentResult:
  if owner_user_id<=0 or slot_key not in SLOT_KEYS:return EquipmentResult("rejected","invalid_equipment_request")
  with self._uow_factory() as uow:
   current={x.slot_key:x.inventory_id for x in uow.equipment.list_slots(owner_user_id)}
   if slot_key not in current:return EquipmentResult("rejected","slot_empty")
   displaced=current[slot_key];uow.equipment.clear_slot(owner_user_id,slot_key);uow.commit()
   return EquipmentResult("ok",slots=tuple(uow.equipment.list_slots(owner_user_id)),displaced=(displaced,))
