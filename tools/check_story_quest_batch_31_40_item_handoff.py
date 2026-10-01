#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json,sqlite3,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
q={x.number:x for x in STORY_QUEST_REGISTRY.values()}
for source,turn,key in ((34,35,"start_path_runemarked_wolf_pelt"),(37,38,"start_path_runemarked_den_token")):
 assert q[source].quest_item.item_key==key
 assert q[source].quest_item.consume_on_completion is False
 assert q[source].quest_item.drop_chance==0.15
 assert len(q[turn].required_quest_items)==1
 assert q[turn].required_quest_items[0].item_key==key
 assert q[turn].required_quest_items[0].consume is True
 assert q[turn].quest_item_consumption=="atomic_exact_once"
doc=json.loads((ROOT/"Квести/ROM_квести_Початок_Шляху_candidate.json").read_text(encoding="utf-8"));rows={int(x["number"]):x for x in doc["quests"]}
assert rows[34]["quest_item"]["consume_on_completion"] is False
assert rows[37]["quest_item"]["consume_on_completion"] is False
con=sqlite3.connect((ROOT/"game.db").resolve().as_uri()+"?mode=ro",uri=True)
try:
 for source_id,turn_id,key in (("start_path_034_runemarked_wolf_pelt","start_path_035_reinforce_the_hunting_party","start_path_runemarked_wolf_pelt"),("start_path_037_trail_to_the_den","start_path_038_heart_of_the_influence","start_path_runemarked_den_token")):
  count=con.execute("""SELECT COUNT(*) FROM user_story_quests s JOIN user_story_quests t ON t.user_id=s.user_id WHERE s.quest_id=? AND s.status='COMPLETED' AND t.quest_id=? AND t.status='ACTIVE' AND NOT EXISTS (SELECT 1 FROM user_story_quest_items i WHERE i.user_id=s.user_id AND i.item_key=? AND i.quantity>0)""",(source_id,turn_id,key)).fetchone()[0]
  assert count==0
finally:con.close()
print("STORY QUEST BATCH 31-40 ITEM HANDOFF: PASS")
