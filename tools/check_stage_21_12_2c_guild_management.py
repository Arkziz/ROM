#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.guild_management_service import *
from rom_v2.domain.guild_core import GuildIdentity
g=GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),),10);u=MemoryManagementUow([g],[GuildApplication(1,1,2)],{2:3},{1:1});r=GuildManagementService(u).accept(1,1);assert r.success and r.guild.role_of(2) is GuildRole.MEMBER;print("Stage 21.12.2c Guild Applications Management smoke: PASS")
