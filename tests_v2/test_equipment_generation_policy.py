from __future__ import annotations
import unittest
from rom_v2.application.equipment_generation_service import EquipmentGenerationError,EquipmentGenerationService
from rom_v2.domain.equipment_generation import EquipmentGenerationRequest,EquipmentGenerationSource,EquipmentIdentity

class IdentityPolicy:
    def __init__(self,allowed=("scout",),subtype="bow"):self.allowed=allowed;self.subtype=subtype
    def select_identity(self,r):return EquipmentIdentity(r.slot_key,self.subtype,"Generated",r.item_level,self.allowed,r.armor_type,1)
class StatsPolicy:
    def __init__(self):self.calls=[]
    def generate_stats(self,r,i):self.calls.append((r.source,r.item_level,i.item_subtype));return {"DEX":r.item_level,"ZERO":0}
class EquipmentGenerationPolicyTests(unittest.TestCase):
    def setUp(self):self.stats=StatsPolicy();self.s=EquipmentGenerationService(IdentityPolicy(),self.stats)
    def test_shop_preserves_class_identity_and_single_level(self):
        x=self.s.for_shop(item_level=7,slot_key="main_hand",rarity="rare",character_class="scout")
        self.assertEqual((x.item_level,x.required_level,x.identity.required_level),(7,7,7));self.assertEqual(x.stats,{"DEX":7.0})
    def test_shop_rejects_wrong_class(self):
        with self.assertRaisesRegex(EquipmentGenerationError,"shop_class_identity_mismatch"):self.s.for_shop(item_level=3,slot_key="main_hand",rarity="common",character_class="mage")
    def test_loot_jewelry_is_universal(self):
        s=EquipmentGenerationService(IdentityPolicy(allowed=(),subtype="ring"),self.stats)
        x=s.for_loot(item_level=5,slot_key="ring",rarity="uncommon");self.assertEqual(x.identity.allowed_classes,())
    def test_loot_weapon_and_armor_identity(self):
        weapon=self.s.for_loot(item_level=4,slot_key="main_hand",rarity="common",character_class="scout")
        armor_service=EquipmentGenerationService(IdentityPolicy(allowed=("scout",),subtype="leather"),self.stats)
        armor=armor_service.for_loot(item_level=4,slot_key="chest",rarity="common",character_class="scout",armor_type="light")
        self.assertEqual(weapon.identity.item_subtype,"bow");self.assertEqual(armor.identity.armor_type,"light")
    def test_identity_and_numeric_generation_are_separate(self):
        self.s.for_loot(item_level=2,slot_key="main_hand",rarity="common",character_class="scout")
        self.assertEqual(self.stats.calls,[(EquipmentGenerationSource.LOOT,2,"bow")])
    def test_required_level_cannot_diverge(self):
        class Bad:
            def select_identity(self,r):return EquipmentIdentity(r.slot_key,"bow","Bad",r.item_level+1,("scout",))
        with self.assertRaisesRegex(EquipmentGenerationError,"identity_level_mismatch"):EquipmentGenerationService(Bad(),self.stats).for_loot(item_level=2,slot_key="main_hand",rarity="common")
    def test_dev_and_simulator_are_consumers(self):
        dev=EquipmentGenerationRequest(EquipmentGenerationSource.DEV,2,"main_hand","common","scout")
        sim=EquipmentGenerationRequest(EquipmentGenerationSource.SIMULATOR,2,"main_hand","common","scout")
        self.assertEqual(self.s.for_dev(dev).source,EquipmentGenerationSource.DEV);self.assertEqual(self.s.for_simulator(sim).source,EquipmentGenerationSource.SIMULATOR)
if __name__=="__main__":unittest.main()
