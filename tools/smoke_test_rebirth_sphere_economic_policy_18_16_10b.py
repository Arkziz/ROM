#!/usr/bin/env python3
from __future__ import annotations
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
premium=(R/"systems/premium_item_policy_system.py").read_text(encoding="utf-8-sig")
auction=(R/"systems/auction_house_system.py").read_text(encoding="utf-8-sig")
trade=(R/"systems/player_interaction_system.py").read_text(encoding="utf-8-sig")
for source in (premium,auction,trade):ast.parse(source)
from systems.premium_item_policy_system import PREMIUM_ITEM_POLICY,DENIED_TRANSFER_ITEM_IDS
from data.rebirth_sphere_policy import get_sphere_economic_policy
assert 501 in PREMIUM_ITEM_POLICY and 501 in DENIED_TRANSFER_ITEM_IDS
assert 504 not in PREMIUM_ITEM_POLICY and 504 not in DENIED_TRANSFER_ITEM_IDS
new_path=get_sphere_economic_policy(501);rebirth=get_sphere_economic_policy(504)
assert new_path=={"premium_bound":True,"character_bound":True,"tradeable":False,"auctionable":False,"mob_drop_eligible":False,"crystal_shop_eligible":True}
assert rebirth=={"premium_bound":False,"character_bound":False,"tradeable":True,"auctionable":True,"mob_drop_eligible":True,"crystal_shop_eligible":False}
assert "AUCTION_PROTECTED_TRANSFER_ITEM_IDS = frozenset((501, 602, 726, 728, 502))" in auction
assert "504" not in ast.get_source_segment(auction,[n for n in ast.parse(auction).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="AUCTION_PROTECTED_TRANSFER_ITEM_IDS" for t in n.targets)][0])
assert "TRADE_BLOCKED_ITEM_IDS = frozenset((501, 602, 726, 728))" in trade
assert "504" not in ast.get_source_segment(trade,[n for n in ast.parse(trade).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="TRADE_BLOCKED_ITEM_IDS" for t in n.targets)][0])
print("[PASS] Stage 18.16.10b Rebirth Sphere economic policy contract")
