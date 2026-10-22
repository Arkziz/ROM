import unittest
from rom_v2.domain.battle import ActorResources,ActorSnapshot,BattleActor,BattleAggregate,BattleMode,BattleStatus
from rom_v2.domain.terminal_paths import *
def battle():
 a=BattleActor(ActorSnapshot("player",1,100,50,{},"player"),ActorResources(100,50));b=BattleActor(ActorSnapshot("mob",None,40,0,{},"mob"),ActorResources(40,0));return BattleAggregate("b1",BattleMode.PVE,"enc1",(a,b),"player")
class TerminalPathsTest(unittest.TestCase):
 def test_victory_exact_order_and_single_output_permission(self):
  out=claim_terminal_path(battle(),TerminalOutcome.VICTORY,"op-v");self.assertTrue(out.accepted);self.assertEqual(out.aggregate.status,BattleStatus.VICTORY);self.assertEqual(out.plan.steps,(SettlementStep.FINALIZE_COMBAT_STATE,SettlementStep.VICTORY_REWARD,SettlementStep.ENEMY_DROPS,SettlementStep.DOWNSTREAM_EVENTS,SettlementStep.PRESENTATION));self.assertEqual(len(out.events),2);self.assertTrue(out.presentation_allowed)
 def test_defeat_has_no_victory_settlement(self):
  out=claim_terminal_path(battle(),TerminalOutcome.DEFEAT,"op-d");self.assertTrue(out.accepted);self.assertIn(SettlementStep.DEFEAT_CONSEQUENCES,out.plan.steps);self.assertNotIn(SettlementStep.VICTORY_REWARD,out.plan.steps);self.assertNotIn(SettlementStep.ENEMY_DROPS,out.plan.steps)
 def test_escape_has_no_victory_settlement(self):
  out=claim_terminal_path(battle(),TerminalOutcome.ESCAPE,"op-e");self.assertTrue(out.accepted);self.assertIn(SettlementStep.ESCAPE_CLEANUP,out.plan.steps);self.assertNotIn(SettlementStep.VICTORY_REWARD,out.plan.steps)
 def test_duplicate_operation_has_no_plan_events_or_message(self):
  first=claim_terminal_path(battle(),TerminalOutcome.VICTORY,"same");again=claim_terminal_path(first.aggregate,TerminalOutcome.VICTORY,"same");self.assertFalse(again.accepted);self.assertTrue(again.duplicate);self.assertIsNone(again.plan);self.assertFalse(again.events);self.assertFalse(again.presentation_allowed)
 def test_competing_terminal_outcome_is_rejected(self):
  first=claim_terminal_path(battle(),TerminalOutcome.ESCAPE,"escape");again=claim_terminal_path(first.aggregate,TerminalOutcome.VICTORY,"victory");self.assertFalse(again.accepted);self.assertTrue(again.duplicate);self.assertFalse(again.events);self.assertFalse(again.presentation_allowed)
 def test_terminal_state_blocks_actions(self):
  self.assertTrue(can_accept_combat_action(battle()));out=claim_terminal_path(battle(),TerminalOutcome.DEFEAT,"defeat");self.assertFalse(can_accept_combat_action(out.aggregate))
 def test_empty_operation_is_unchanged_failure(self):
  original=battle();out=claim_terminal_path(original,TerminalOutcome.VICTORY," " );self.assertFalse(out.accepted);self.assertEqual(out.aggregate,original);self.assertFalse(out.events);self.assertFalse(out.presentation_allowed)
if __name__=="__main__":unittest.main()
