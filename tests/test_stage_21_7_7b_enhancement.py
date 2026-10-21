from random import Random
from rom_v2.domain.enhancement import *
from rom_v2.application.enhancement_service import EnhancementService
class G:
 def __init__(self,item,resources=True):self.item=item;self.resources=resources;self.done={}
 def get_owned_item(self,u,i):return self.item if self.item and self.item.user_id==u and self.item.inventory_id==i else None
 def is_operation_completed(self,u,o):return self.done.get((u,o))
 def perform_attempt_atomically(self,c,q,ok,after):
  if not self.resources:return EnhancementResult(False,level_before=q.item.refine_level,level_after=q.item.refine_level,failure=EnhancementFailure.INSUFFICIENT_RESOURCES)
  r=EnhancementResult(True,ok,q.item.refine_level,after);self.done[(c.user_id,c.operation_id)]=r;self.item=EnhancementItem(q.item.user_id,q.item.inventory_id,q.item.kind,after,q.item.rarity,q.item.durability);return r
def test_exact_v1_tables_and_stats():
 assert get_refine_success_chance("weapon",3)==80 and get_refine_success_chance("armor",2)==70
 assert get_refine_success_chance("armor",5,True)==100
 assert apply_weapon_refine_to_damage(100,10)==200
 assert get_armor_refine_hp_bonus_percent(6,"epic")==5.2
def test_caps_and_failure_levels():
 assert get_refine_max_level("weapon")==10 and get_refine_max_level("armor")==6
 assert get_refine_failure_level("weapon",7)==6 and get_refine_failure_level("armor",4)==3
def test_atomic_no_resource_no_mutation():
 g=G(EnhancementItem(1,9,"weapon",3),False);r=EnhancementService(g,Random(1)).attempt(EnhancementCommand(1,9,"op"));assert r.failure is EnhancementFailure.INSUFFICIENT_RESOURCES and g.item.refine_level==3
def test_reservation_and_idempotent_replay():
 b=G(EnhancementItem(1,9,"armor",2,reserved=True));assert EnhancementService(b,Random(1)).attempt(EnhancementCommand(1,9,"x")).failure is EnhancementFailure.RESERVED
 g=G(EnhancementItem(1,9,"weapon",0));s=EnhancementService(g,Random(1));a=s.attempt(EnhancementCommand(1,9,"same"));b=s.attempt(EnhancementCommand(1,9,"same"));assert a.success and b.replayed and b.level_after==a.level_after
