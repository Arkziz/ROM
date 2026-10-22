import unittest
from rom_v2.domain.central_loot import *

class SeqRng:
 def __init__(self,*values):self.values=list(values);self.calls=0
 def random(self):self.calls+=1;return self.values.pop(0)

def rule(key,chance=1.0,candidates=None,enabled=True):
 return LootRule(key,"mob",(("normal",chance),("elite",chance),("boss",chance)),tuple(candidates or (LootCandidate(key),)),enabled)

class CentralLootPlannerTests(unittest.TestCase):
 def test_source_order_and_independent_rolls(self):
  rng=SeqRng(.1,.9);groups=(LootGroup("g",(rule("a",.5),rule("b",.5))),)
  out=CentralLootPlanner().plan(enemy_class="normal",enemy_level=3,player_class="scout",location_key="x",rules=groups,rng=rng)
  self.assertEqual([x.key for x in out.immutable_loot_commands],["a"]);self.assertEqual([x.outcome for x in out.roll_trace],["selected","miss"]);self.assertEqual(rng.calls,2)
 def test_weighted_selection_preserves_draw_order(self):
  rng=SeqRng(.1,.8);r=rule("r",1,(LootCandidate("a",1),LootCandidate("b",3)))
  out=CentralLootPlanner().plan(enemy_class="elite",enemy_level=2,player_class="mage",location_key="x",rules=(LootGroup("g",(r,)),),rng=rng)
  self.assertEqual(out.immutable_loot_commands[0].key,"b");self.assertEqual(rng.calls,2)
 def test_single_candidate_consumes_no_selection_draw(self):
  rng=SeqRng(.2);out=CentralLootPlanner().plan(enemy_class="boss",enemy_level=5,player_class="knight",location_key="x",rules=(LootGroup("g",(rule("a"),)),),rng=rng)
  self.assertEqual(rng.calls,1);self.assertIsNone(out.roll_trace[0].selection_roll)
 def test_group_limit_stops_additional_rng_draws(self):
  rng=SeqRng(.1);out=CentralLootPlanner().plan(enemy_class="normal",enemy_level=1,player_class="warrior",location_key="x",rules=(LootGroup("g",(rule("a"),rule("b")),1),),rng=rng)
  self.assertEqual(rng.calls,1);self.assertEqual([x.outcome for x in out.roll_trace],["selected","group_limit"])
 def test_disabled_rule_consumes_no_rng(self):
  rng=SeqRng();out=CentralLootPlanner().plan(enemy_class="normal",enemy_level=1,player_class="priest",location_key="x",rules=(LootGroup("g",(rule("a",enabled=False),)),),rng=rng)
  self.assertEqual(rng.calls,0);self.assertEqual(out.roll_trace[0].outcome,"disabled")
 def test_equipment_is_deferred_request_not_item(self):
  rng=SeqRng(.0);r=rule("eq",1,(LootCandidate("armor",1,1,"equipment_request"),))
  out=CentralLootPlanner().plan(enemy_class="boss",enemy_level=7,player_class="rogue",location_key="x",rules=(LootGroup("g",(r,)),),rng=rng)
  self.assertFalse(out.immutable_loot_commands);self.assertEqual(out.equipment_generation_requests[0].request_key,"armor")
 def test_invalid_configuration_fails_before_rng(self):
  rng=SeqRng(.1);bad=LootRule("r","g",(("normal",1.1),),(LootCandidate("a"),))
  with self.assertRaises(CentralLootConfigurationError):CentralLootPlanner().plan(enemy_class="normal",enemy_level=1,player_class="x",location_key="x",rules=(LootGroup("g",(bad,)),),rng=rng)
  self.assertEqual(rng.calls,0)
 def test_contract_has_no_premium_or_inventory_input(self):
  names=CentralLootPlanner.plan.__annotations__
  self.assertNotIn("premium",names);self.assertNotIn("inventory",names)

if __name__=="__main__":unittest.main()
