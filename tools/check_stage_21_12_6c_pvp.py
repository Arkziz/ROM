#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.pvp_service import *
from dataclasses import replace
class Resolver:
 def resolve(self,b,actions):return replace(b,round_number=2,revision=2)
b=V2PvpBattleState(1,1,(V2PvpParticipantSnapshot(10,"a","warrior",1,100,100,"rage",0),V2PvpParticipantSnapshot(20,"b","mage",1,80,80,"mana",100)));u=InMemoryV2PvpLifecycleUow([b]);s=V2PvpLifecycleService(u,Resolver());assert s.submit(V2PvpActionIntent(1,1,1,10,"attack")).success;assert s.submit(V2PvpActionIntent(1,1,1,20,"guard")).resolution_required;assert s.resolve(1,1).battle.round_number==2;print("Stage 21.12.6c PvP smoke: PASS")
