#!/usr/bin/env python3
from pathlib import Path
from decimal import Decimal
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.auction_service import *
snap=AuctionSnapshot(1,101,1,"equipment",permanent_id=10001);lot=AuctionLot(1,10,snap,Decimal("25"),expires_at=10);u=MemoryAuctionUow([lot]);s=AuctionService(u);r=s.buy(1,20,0);assert r.success and r.lot.status is LotStatus.SOLD_UNCLAIMED and u.purchases==[(20,1)];assert s.buy(1,20,0).reason=="lot_unavailable";print("Stage 21.12.5c Auction smoke: PASS")
