import unittest
from dataclasses import replace
from rom_v2.application.pvp_service import *
def battle():return V2PvpBattleState(1,7,(V2PvpParticipantSnapshot(10,"a","warrior",5,100,100,"rage",0),V2PvpParticipantSnapshot(20,"b","mage",5,80,80,"mana",100)),deadline_at=10)
class Resolver:
 def resolve(self,b,actions):return replace(b,round_number=b.round_number+1,revision=b.revision+1)
class PvpTest(unittest.TestCase):
 def test_idempotent_create(self):
  u=InMemoryV2PvpLifecycleUow();s=V2PvpLifecycleService(u,Resolver());self.assertTrue(s.create_from_accepted(battle()).changed);self.assertEqual(s.create_from_accepted(battle()).reason,"already_created")
 def test_revision_and_round_ready(self):
  b=battle();u=InMemoryV2PvpLifecycleUow([b]);s=V2PvpLifecycleService(u,Resolver());a=V2PvpActionIntent(1,1,1,10,"attack");self.assertFalse(s.submit(a).resolution_required);self.assertTrue(s.submit(V2PvpActionIntent(1,1,1,20,"guard")).resolution_required);self.assertEqual(s.submit(V2PvpActionIntent(1,1,9,10,"attack")).reason,"stale_revision")
 def test_claim_and_resolution(self):
  b=battle();u=InMemoryV2PvpLifecycleUow([b]);s=V2PvpLifecycleService(u,Resolver());r=s.resolve(1,1);self.assertEqual(r.battle.round_number,2);self.assertEqual(r.battle.revision,2)
 def test_duplicate_claim_same_revision(self):
  b=battle();u=InMemoryV2PvpLifecycleUow([b]);u.claims.add((1,1,1));s=V2PvpLifecycleService(u,Resolver());self.assertEqual(s.resolve(1,1).reason,"already_claimed")
 def test_timeout_exact_once_history(self):
  b=battle();u=InMemoryV2PvpLifecycleUow([b]);s=V2PvpLifecycleService(u,Resolver());r=s.timeout(1,{10});self.assertEqual(r.battle.winner_id,20);self.assertEqual(len(u.history),2);self.assertEqual(s.timeout(1,{10}).reason,"battle_unavailable")
 def test_double_timeout(self):
  b=battle();u=InMemoryV2PvpLifecycleUow([b]);r=V2PvpLifecycleService(u,Resolver()).timeout(1,{10,20});self.assertIsNone(r.battle.winner_id);self.assertEqual(r.battle.result_reason,"double_timeout")
 def test_recovery(self):
  u=InMemoryV2PvpLifecycleUow([battle()]);self.assertEqual(V2PvpLifecycleService(u,Resolver()).recover()[0].outcome,"resumed")
if __name__=="__main__":unittest.main()
