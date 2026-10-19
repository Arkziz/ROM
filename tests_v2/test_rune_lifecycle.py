from __future__ import annotations
import copy, unittest
from rom_v2.application.services.rune_lifecycle import RuneLifecycleService
from rom_v2.domain.runes import RuneDefinition,RuneEquipmentState,RuneFailure

class MemoryGateway:
    def __init__(self):
        self.equipment=RuneEquipmentState(10,1,"chest",2,True,100,{})
        self.runes={101:1}; self.extractors={201:1}; self.balance=50; self.reserved=False
    def load_equipment(self,u,i): return self.equipment if (u,i)==(1,10) else None
    def rune_quantity(self,u,i): return self.runes.get(i,0)
    def is_reserved(self,u,i): return self.reserved
    def extractor_quantity(self,u,i): return self.extractors.get(i,0)
    def gold(self,u): return self.balance
    def commit_insert(self,*,expected,updated,rune_item_id):
        if self.equipment!=expected or self.runes.get(rune_item_id,0)<1:return False
        self.runes[rune_item_id]-=1; self.equipment=updated; return True
    def commit_extract(self,*,expected,updated,rune_item_id,extractor_item_id,gold_cost):
        if self.equipment!=expected:return False
        if extractor_item_id is not None:
            if self.extractors.get(extractor_item_id,0)<1:return False
            self.extractors[extractor_item_id]-=1
        if self.balance<gold_cost:return False
        self.balance-=gold_cost; self.runes[rune_item_id]=self.runes.get(rune_item_id,0)+1
        self.equipment=updated; return True

class RuneLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.g=MemoryGateway(); self.s=RuneLifecycleService(self.g)
        self.r=RuneDefinition(101,"rune_sta_1","sta",1,2.0,("warrior",))
    def test_atomic_insert_extract_and_restart_shape(self):
        inserted=self.s.insert(user_id=1,equipment_inventory_id=10,slot_index=0,rune=self.r,character_class="warrior")
        self.assertTrue(inserted.success); self.assertEqual(1,len(self.s.contributions(self.g.equipment)))
        persisted=copy.deepcopy(self.g.equipment)
        self.assertEqual(101,persisted.sockets[0].rune.item_id)
        extracted=self.s.extract(user_id=1,equipment_inventory_id=10,slot_index=0,extractor_item_id=201,gold_cost=7)
        self.assertTrue(extracted.success); self.assertEqual(43,self.g.balance); self.assertEqual(1,self.g.runes[101])
    def test_guards_fail_before_mutation(self):
        before=copy.deepcopy(self.g.equipment); self.g.reserved=True
        result=self.s.insert(user_id=1,equipment_inventory_id=10,slot_index=0,rune=self.r,character_class="warrior")
        self.assertEqual(RuneFailure.RESERVED,result.code); self.assertEqual(before,self.g.equipment)
        self.g.reserved=False
        result=self.s.insert(user_id=1,equipment_inventory_id=10,slot_index=9,rune=self.r,character_class="warrior")
        self.assertEqual(RuneFailure.INVALID_SOCKET,result.code)
    def test_class_occupied_durability_and_exact_owner(self):
        self.assertFalse(self.s.insert(user_id=2,equipment_inventory_id=10,slot_index=0,rune=self.r,character_class="warrior").success)
        self.assertEqual(RuneFailure.INCOMPATIBLE_CLASS,self.s.insert(user_id=1,equipment_inventory_id=10,slot_index=0,rune=self.r,character_class="mage").code)
        self.assertTrue(self.s.insert(user_id=1,equipment_inventory_id=10,slot_index=0,rune=self.r,character_class="warrior").success)
        self.assertEqual(RuneFailure.SOCKET_OCCUPIED,self.s.insert(user_id=1,equipment_inventory_id=10,slot_index=0,rune=self.r,character_class="warrior").code)
        broken=RuneEquipmentState(10,1,"chest",2,True,0,self.g.equipment.sockets)
        self.assertEqual((),self.s.contributions(broken))
if __name__=="__main__": unittest.main()
