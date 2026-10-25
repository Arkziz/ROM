import unittest
from decimal import Decimal
from rom_v2.application.auction_service import *
def snap(i=1):return AuctionSnapshot(i,100+i,1,"equipment",permanent_id=10000+i,durability=90,refine_level=2,runes=("sta",))
def lot(i=1,seller=10,status=LotStatus.ACTIVE,expires=20):return AuctionLot(i,seller,snap(i),Decimal("10.999"),status,expires_at=expires)
class AuctionTest(unittest.TestCase):
 def test_price_rounding_and_bounds(self):self.assertEqual(normalize_price("10.999"),Decimal("10.99"));self.assertRaises(ValueError,normalize_price,"0.99")
 def test_listing_and_duplicate(self):
  u=MemoryAuctionUow();s=AuctionService(u);r=s.list_item(1,10,snap(),"12.34",0);self.assertTrue(r.success);self.assertEqual(u.consumed,[1]);self.assertEqual(s.list_item(1,10,snap(),"12.34",0).reason,"duplicate_lot")
 def test_limit(self):
  u=MemoryAuctionUow([lot(i,10) for i in range(1,21)]);self.assertEqual(AuctionService(u).list_item(30,10,snap(30),"5",0).reason,"active_limit")
 def test_browse_and_self_purchase(self):
  u=MemoryAuctionUow([lot(1,10),lot(2,20)]);s=AuctionService(u);self.assertEqual([x.lot_id for x in s.browse(10,now=0).items],[2]);self.assertEqual(s.buy(1,10,0).reason,"self_purchase")
 def test_purchase_and_replay(self):
  u=MemoryAuctionUow([lot()]);s=AuctionService(u);r=s.buy(1,20,0);self.assertEqual(r.lot.status,LotStatus.SOLD_UNCLAIMED);self.assertEqual(u.purchases,[(20,1)]);self.assertEqual(s.buy(1,20,0).reason,"lot_unavailable")
 def test_sale_ack_exact_once(self):
  u=MemoryAuctionUow([lot(status=LotStatus.SOLD_UNCLAIMED)]);s=AuctionService(u);self.assertTrue(s.acknowledge_sale(1,10).changed);self.assertEqual(s.acknowledge_sale(1,10).reason,"already_claimed")
 def test_expiry_claim_bag_full_and_replay(self):
  u=MemoryAuctionUow([lot(expires=1)]);s=AuctionService(u);self.assertEqual(s.expire(2),(1,));u.restore_error="bag_full";self.assertEqual(s.claim_expired(1,10).reason,"bag_full");u.restore_error=None;self.assertTrue(s.claim_expired(1,10).changed);self.assertEqual(s.claim_expired(1,10).reason,"already_claimed");self.assertEqual(u.restored,[(10,1)])
 def test_cancel_exact_once(self):
  u=MemoryAuctionUow([lot()]);s=AuctionService(u);self.assertTrue(s.cancel(1,10).changed);self.assertEqual(s.cancel(1,10).reason,"already_terminal");self.assertEqual(u.restored,[(10,1)])
if __name__=="__main__":unittest.main()
