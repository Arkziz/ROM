import unittest
from datetime import datetime,timedelta,timezone
from rom_v2.application.travel_service import *
from rom_v2.domain.travel_aggregate import TravelStatus
class T(unittest.TestCase):
 def setUp(self):self.n=datetime(2026,1,1,tzinfo=timezone.utc);self.u=MemoryUow({1:{"location":"city","level":6}});self.b=MemoryBusy();self.s=TravelService(self.u,self.b)
 def test_start_complete(self):
  t=self.s.start(1,"start_path",self.n).travel;self.assertEqual((t.revision,(t.arrival_at-t.started_at).seconds),(1,20));r=self.s.complete(t.travel_id,self.n+timedelta(seconds=20));self.assertTrue(r.success);self.assertEqual((r.travel.status,self.u.players[1]["location"]),(TravelStatus.ARRIVED,"start_path"))
 def test_rejections(self):
  self.b.data[1]=1;self.assertEqual(self.s.start(1,"start_path",self.n).reason,"player_busy");self.b.data.clear();self.assertEqual(self.s.start(1,"dark_forest",self.n).reason,"not_adjacent")
 def test_cancel_revision(self):
  t=self.s.start(1,"start_path",self.n).travel;self.assertEqual(self.s.cancel(1,t.travel_id,2,self.n).reason,"stale_revision");r=self.s.cancel(1,t.travel_id,1,self.n);self.assertEqual((r.travel.status,r.travel.revision),(TravelStatus.CANCELLED,2));self.assertEqual(self.s.cancel(1,t.travel_id,2,self.n).reason,"already_terminal")
 def test_source_drift(self):
  t=self.s.start(1,"start_path",self.n).travel;self.u.players[1]["location"]="dark_forest";r=self.s.complete(t.travel_id,self.n+timedelta(seconds=20));self.assertEqual((r.reason,r.travel.status),("source_changed",TravelStatus.FAILED))
 def test_recovery_limit(self):
  a=self.s.start(1,"start_path",self.n).travel;self.u.players[2]={"location":"city","level":6};b=self.s.start(2,"start_path",self.n+timedelta(seconds=1)).travel;r=self.s.recover_due(self.n+timedelta(seconds=30),1);self.assertEqual((len(r),r[0].travel.travel_id,self.u.get(b.travel_id).status),(1,a.travel_id,TravelStatus.ACTIVE))
if __name__=="__main__":unittest.main()
