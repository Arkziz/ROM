#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.guild_contract_history_service import *
from rom_v2.domain.guild_contract_history import *
from rom_v2.domain.guild_core import GuildCore,GuildIdentity,GuildMember,GuildRole
g=GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),),10);u=MemoryContractHistoryUow([g]);s=GuildContractHistoryService(u);r=s.apply(GuildContractCompletion("contract:1",1,"Вовк"));p,e=s.history(1,1);assert r.success and e is None and p.items[0].target_name=="Вовк";print("Stage 21.12.3c Guild Contracts History smoke: PASS")
