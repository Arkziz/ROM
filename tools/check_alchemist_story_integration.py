#!/usr/bin/env python3
from pathlib import Path
import ast
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
s=(ROOT/'handlers/city.py').read_text(encoding="utf-8-sig")
assert s.count('send_story_npc_if_present(bot, message, "alchemist")')==1
assert "Алхімік готує та продає зілля" in s and "Купити зілля" in s and "Продати зілля" in s
ast.parse(s,'handlers/city.py')
from data.story_quest_content import STORY_QUEST_REGISTRY
q={x.number:x for x in STORY_QUEST_REGISTRY.values()}
assert q[14].giver_npc_id==q[14].turn_in_npc_id=="alchemist"
assert q[14].quest_type.value=="TURN_IN"
assert q[14].required_quest_items[0].item_key=="start_path_runic_crystal_fragment"
assert q[16].giver_npc_id==q[16].turn_in_npc_id=="alchemist"
assert q[16].required_quest_items[0].item_key=="start_path_runic_dust_sample"
print("ALCHEMIST STORY INTEGRATION: PASS")
