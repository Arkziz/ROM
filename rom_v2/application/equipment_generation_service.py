"""Single orchestration owner for shop, loot, DEV and simulator generation."""
from __future__ import annotations
from rom_v2.application.equipment_generation_ports import EquipmentIdentityPolicy,EquipmentStatPolicy
from rom_v2.domain.equipment_generation import EquipmentGenerationRequest,EquipmentGenerationSource,GeneratedEquipment,JEWELRY_SLOTS

class EquipmentGenerationError(RuntimeError):pass

class EquipmentGenerationService:
    """Coordinate source-aware identity selection and canonical numeric generation.

    Formulas remain behind audited policy ports so V2 does not invent or duplicate
    V1 stat calculations. Every consumer passes one canonical item_level value.
    """
    def __init__(self,identity_policy:EquipmentIdentityPolicy,stat_policy:EquipmentStatPolicy)->None:
        self._identity_policy=identity_policy;self._stat_policy=stat_policy
    def generate(self,request:EquipmentGenerationRequest)->GeneratedEquipment:
        try:
            identity=self._identity_policy.select_identity(request)
            self._validate_identity(request,identity)
            stats=self._stat_policy.generate_stats(request,identity)
            return GeneratedEquipment(source=request.source,item_level=request.item_level,identity=identity,stats=stats,rarity=request.rarity)
        except EquipmentGenerationError:raise
        except (TypeError,ValueError,KeyError) as exc:raise EquipmentGenerationError(str(exc)) from exc
    def for_shop(self,*,item_level:int,slot_key:str,rarity:str,character_class:str,armor_type:str|None=None,identity_hint:str|None=None)->GeneratedEquipment:
        return self.generate(EquipmentGenerationRequest(EquipmentGenerationSource.SHOP,item_level,slot_key,rarity,character_class,armor_type,identity_hint))
    def for_loot(self,*,item_level:int,slot_key:str,rarity:str,character_class:str|None=None,armor_type:str|None=None,identity_hint:str|None=None)->GeneratedEquipment:
        return self.generate(EquipmentGenerationRequest(EquipmentGenerationSource.LOOT,item_level,slot_key,rarity,character_class,armor_type,identity_hint))
    def for_dev(self,request:EquipmentGenerationRequest)->GeneratedEquipment:
        if request.source is not EquipmentGenerationSource.DEV:raise EquipmentGenerationError("dev_source_required")
        return self.generate(request)
    def for_simulator(self,request:EquipmentGenerationRequest)->GeneratedEquipment:
        if request.source is not EquipmentGenerationSource.SIMULATOR:raise EquipmentGenerationError("simulator_source_required")
        return self.generate(request)
    @staticmethod
    def _validate_identity(request:EquipmentGenerationRequest,identity)->None:
        if identity.slot_key!=request.slot_key:raise EquipmentGenerationError("identity_slot_mismatch")
        if identity.required_level!=request.item_level:raise EquipmentGenerationError("identity_level_mismatch")
        if request.source is EquipmentGenerationSource.SHOP and request.character_class not in identity.allowed_classes:raise EquipmentGenerationError("shop_class_identity_mismatch")
        if request.slot_key in JEWELRY_SLOTS and identity.allowed_classes:raise EquipmentGenerationError("dropped_jewelry_not_universal")
        if request.armor_type!=identity.armor_type:raise EquipmentGenerationError("armor_type_mismatch")
