#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.guild_core_service import *
i=GuildIdentity("Варта","варта","ВРТ","врт","🏰");u=MemoryGuildUow({1:100.0});r=GuildCoreService(u).create(1,3,i);assert r.success and r.gold_balance==50.0 and r.guild.member_limit==10 and r.guild.role_of(1) is GuildRole.LEADER;print("Stage 21.12.1c Guild Core smoke: PASS")
