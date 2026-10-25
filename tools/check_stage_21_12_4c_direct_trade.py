#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.direct_trade_service import *
t=DirectTrade(1,10,20,"town",initiator_offer=TradeOffer(10),recipient_offer=TradeOffer(20));u=MemoryDirectTradeUow([t],{10:"town",20:"town"});s=DirectTradeService(u);assert s.ready(1,10,0).success and s.ready(1,20,0).success;assert s.confirm(1,10,0).success and s.confirm(1,20,0).trade.status is TradeStatus.COMPLETED;assert u.settlements==[1];print("Stage 21.12.4c Direct Trade smoke: PASS")
