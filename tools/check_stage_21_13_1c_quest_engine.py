#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.quest_engine_service import *
class S:
 def progress_delta(self,d,e,u):return 1
d=V2QuestDefinition(900001,"fixture",1,V2QuestObjectiveType.TALK,reward=V2QuestReward(1,1));u=InMemoryV2QuestEngineUow();s=V2QuestEngineService(u,{x:S() for x in V2QuestObjectiveType});r=s.accept(1,d,1,"fixture");r=s.apply_event(1,d,"event","id",r.progress.revision);r=s.turn_in(1,d,r.progress.revision);assert r.progress.state is V2QuestState.COMPLETED and len(u.reward_plans)==1;print("Stage 21.13.1c Quest Engine smoke: PASS")
