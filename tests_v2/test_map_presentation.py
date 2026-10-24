import unittest
from datetime import datetime,timedelta,timezone
from rom_v2.application.map_presentation import *
from rom_v2.domain.travel_aggregate import TravelAggregate,TravelStatus
class MapPresentationTest(unittest.TestCase):
 def test_ready_order_and_unlock(self):
  v=build_map_view("start_path",5);self.assertEqual([d.node_id for d in v.directions],["city","dark_forest"]);self.assertTrue(v.directions[0].unlocked);self.assertFalse(v.directions[1].unlocked);self.assertIsNone(v.directions[1].action);self.assertEqual(v.directions[1].label,"🌲 Темний Бір")
 def test_technical_ids_not_in_labels(self):
  v=build_map_view("city",6);labels=[v.current_label,*[d.label for d in v.directions],*[a.label for a in v.actions]];self.assertNotIn("start_path"," ".join(labels));self.assertEqual(node_label("missing"),UNKNOWN_PLACE)
 def test_callback_roundtrip_and_fail_closed(self):
  for c in (CallbackCommand("open"),CallbackCommand("players"),CallbackCommand("preview",node_id="start_path"),CallbackCommand("cancel",travel_id=7,revision=2)):self.assertEqual(decode_callback(encode_callback(c)),c)
  for bad in ("","map:start:missing","map:cancel:x:1","map:cancel:1:0","other:open"):self.assertIsNone(decode_callback(bad))
 def test_in_transit_countdown_and_actions(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc);t=TravelAggregate(3,1,"city","start_path",TravelStatus.ACTIVE,2,now,now+timedelta(seconds=20));v=build_map_view("city",6,active_travel=t,now=now+timedelta(seconds=1,microseconds=1));self.assertEqual((v.mode,v.active_travel.remaining_seconds),(MapMode.IN_TRANSIT,19));self.assertEqual(v.directions,());self.assertEqual(decode_callback(v.active_travel.cancel.callback_data).revision,2)
 def test_countdown_never_negative(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc);t=TravelAggregate(3,1,"city","start_path",TravelStatus.ACTIVE,1,now,now+timedelta(seconds=20));self.assertEqual(build_map_view("city",6,active_travel=t,now=now+timedelta(seconds=21)).active_travel.remaining_seconds,0)
if __name__=="__main__":unittest.main()
