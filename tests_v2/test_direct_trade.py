import unittest
from rom_v2.application.direct_trade_service import *
def trade():return DirectTrade(1,10,20,"town",initiator_offer=TradeOffer(10),recipient_offer=TradeOffer(20))
class DirectTradeTest(unittest.TestCase):
 def setUp(self):self.u=MemoryDirectTradeUow([trade()],{10:"town",20:"town"});self.s=DirectTradeService(self.u)
 def test_offer_revision_and_no_change(self):
  offer=TradeOffer(10,(TradeItemSnapshot(1,101,1),),5);r=self.s.set_offer(1,10,offer,0);self.assertEqual(r.trade.revision,1);self.assertFalse(self.s.set_offer(1,10,offer,1).changed)
 def test_item_policy(self):
  bad=TradeOffer(10,(TradeItemSnapshot(1,101,1,item_key="firius_token"),));self.assertEqual(self.s.set_offer(1,10,bad,0).reason,"blocked_item")
 def test_stale_and_eligibility(self):
  self.assertEqual(self.s.ready(1,10,9).reason,"stale_revision");self.u.locations[20]="forest";self.assertEqual(self.s.ready(1,10,0).reason,"location_changed")
 def test_two_phase_settlement_and_replay(self):
  a=self.s.ready(1,10,0);b=self.s.ready(1,20,0);self.assertTrue(a.success and b.success);self.s.confirm(1,10,0);done=self.s.confirm(1,20,0);self.assertTrue(done.settlement_required);self.assertEqual(self.u.settlements,[1]);self.assertEqual(self.s.confirm(1,20,0).reason,"already_completed")
 def test_edit_invalidates(self):
  self.s.ready(1,10,0);self.s.ready(1,20,0);r=self.s.return_to_editing(1,10,0);self.assertEqual(r.trade.revision,1);self.assertFalse(r.trade.initiator_ready)
 def test_cancel_replay(self):
  self.assertTrue(self.s.cancel(1,10).changed);r=self.s.cancel(1,20);self.assertEqual(r.reason,"already_terminal");self.assertEqual(self.u.releases,[1])
 def test_restart_recovery(self):
  self.u.trades[2]=DirectTrade(2,30,40,"town",initiator_ready=True);self.u.locations.update({30:"town",40:"town"});self.u.expired_ids.add(1);out=self.s.recover();self.assertIn((1,"expired"),out);self.assertIn((2,"preserved"),out);self.assertFalse(self.u.trade(2).initiator_ready)
if __name__=="__main__":unittest.main()
