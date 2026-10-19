"""Ports that keep V1 identity and numeric-stat policies separate."""
from __future__ import annotations
from typing import Mapping,Protocol
from rom_v2.domain.equipment_generation import EquipmentGenerationRequest,EquipmentIdentity

class EquipmentIdentityPolicy(Protocol):
    def select_identity(self,request:EquipmentGenerationRequest)->EquipmentIdentity:...
class EquipmentStatPolicy(Protocol):
    def generate_stats(self,request:EquipmentGenerationRequest,identity:EquipmentIdentity)->Mapping[str,float]:...
class EquipmentGenerationRandom(Protocol):
    def random(self)->float:...
