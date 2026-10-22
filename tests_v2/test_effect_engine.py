import unittest
from rom_v2.domain.effect_engine import *
class EffectEngineTest(unittest.TestCase):
 def test_replace_policy_and_input_immutable(self):
  old=Effect("hot",EffectKind.HOT,2,5);state={"hot":old};new=Effect("hot",EffectKind.HOT,2,7);out=apply_effect(state,new,ReapplyPolicy.REPLACE);self.assertEqual(out.effects["hot"],new);self.assertEqual(state,{"hot":old})
 def test_stronger_longer_v1_policy(self):
  old=Effect("dot",EffectKind.DOT,2,10);state={"dot":old}
  self.assertEqual(apply_effect(state,Effect("dot",EffectKind.DOT,5,8),ReapplyPolicy.STRONGER_LONGER).outcome,ApplyOutcome.KEPT_STRONGER)
  refreshed=apply_effect(state,Effect("dot",EffectKind.DOT,5,10),ReapplyPolicy.STRONGER_LONGER);self.assertEqual(refreshed.outcome,ApplyOutcome.REFRESHED);self.assertEqual(refreshed.effects["dot"].turns,5)
  stronger=apply_effect(state,Effect("dot",EffectKind.DOT,1,12),ReapplyPolicy.STRONGER_LONGER);self.assertEqual(stronger.effects["dot"].turns,2);self.assertEqual(stronger.effects["dot"].power,12)
 def test_tick_order_fresh_skip_and_expiration(self):
  state={"new":Effect("new",EffectKind.DOT,2,3,fresh=True),"hot":Effect("hot",EffectKind.HOT,1,4)};out=tick_start(state)
  self.assertFalse(out.effects["new"].fresh);self.assertEqual(out.effects["new"].turns,2);self.assertNotIn("hot",out.effects);self.assertEqual([e.kind for e in out.events],[EffectEventKind.HEAL,EffectEventKind.EXPIRED])
 def test_priest_one_immediate_plus_two_ticks_contract(self):
  state={};state=apply_effect(state,Effect("priest_healing_blessing_hot",EffectKind.HOT,2,9),ReapplyPolicy.REPLACE).effects
  first=tick_start(state);second=tick_start(first.effects);self.assertEqual(sum(e.amount for e in first.events+second.events if e.kind is EffectEventKind.HEAL),18);self.assertFalse(second.effects)
 def test_shield_and_failure_atomicity(self):
  shield=Effect("shield",EffectKind.SHIELD,3,10);state={"shield":shield};remaining,out=absorb_shield(state,6);self.assertEqual(remaining,0);self.assertEqual(out.effects["shield"].power,4);self.assertEqual(state["shield"].power,10)
  remaining,failed=absorb_shield(state,-1);self.assertEqual(remaining,-1);self.assertFalse(failed.success);self.assertEqual(failed.effects,state)
if __name__=="__main__":unittest.main()
