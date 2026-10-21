from rom_v2.application.durability_service import DurabilityService
from rom_v2.domain.durability import *

class MemoryGateway:
    def __init__(self,rows,gold=100):self.rows={x.inventory_id:x for x in rows};self.gold=gold
    def list_equipped(self,user_id):return tuple(self.rows.values())
    def repair_atomically(self,user_id,quotes):
        price=sum(x.cost for x in quotes)
        if self.gold<price:return RepairResult(False,failure=RepairFailure.INSUFFICIENT_GOLD)
        self.gold-=price
        for q in quotes:
            old=self.rows[q.inventory_id];self.rows[q.inventory_id]=EquippedDurability(old.inventory_id,100,old.rarity,old.reserved)
        return RepairResult(True,price,tuple(q.inventory_id for q in quotes))
    def damage_equipped_atomically(self,user_id,amount):
        changed=[]
        for iid,old in tuple(self.rows.items()):
            new=damage_durability(old.durability,amount)
            if new!=old.durability:
                self.rows[iid]=EquippedDurability(iid,new,old.rarity,old.reserved);changed.append(iid)
        return tuple(changed)

def test_v1_formula_multipliers_and_clamp():
    assert calculate_repair_cost(90,"common")==1
    assert calculate_repair_cost(90,"uncommon")==1
    assert calculate_repair_cost(90,"rare")==4
    assert calculate_repair_cost(90,"epic")==9
    assert damage_on_death(3)==0 and damage_on_death(100)==95
    assert contributes_stats(1) and not contributes_stats(0)

def test_exact_item_repair_and_insufficient_funds_no_mutation():
    gateway=MemoryGateway([EquippedDurability(11,50,"epic")],gold=1)
    result=DurabilityService(gateway).repair_one(7,11)
    assert result.failure is RepairFailure.INSUFFICIENT_GOLD
    assert gateway.gold==1 and gateway.rows[11].durability==50

def test_reserved_fail_closed_and_repair_all_atomic_boundary():
    blocked=MemoryGateway([EquippedDurability(1,90,"common",True)])
    assert DurabilityService(blocked).repair_all(2).failure is RepairFailure.RESERVED
    gateway=MemoryGateway([EquippedDurability(1,90,"common"),EquippedDurability(2,90,"epic")],gold=10)
    result=DurabilityService(gateway).repair_all(2)
    assert result.success and result.repaired_inventory_ids==(1,2)
    assert gateway.gold==0 and all(x.durability==100 for x in gateway.rows.values())

def test_death_damages_equipped_only_through_atomic_gateway():
    gateway=MemoryGateway([EquippedDurability(9,4,"rare")])
    changed=DurabilityService(gateway).damage_equipped_on_death(3)
    assert changed==(9,) and gateway.rows[9].durability==0
