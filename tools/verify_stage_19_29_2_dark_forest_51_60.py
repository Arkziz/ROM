from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_hierarchy import validate_story_hierarchy_metadata
q=sorted(STORY_QUEST_REGISTRY.values(),key=lambda x:x.number)
assert [x.number for x in q]==list(range(1,61)) and q[50].previous_quest_id==q[49].quest_id
assert all(x.location_id=="dark_forest" and x.unlock_level==6 and x.reward.exp==66 and abs(x.reward.gold-1.84)<1e-9 for x in q[50:])
assert [q[n-1].target_quantity for n in (52,56,59)]==[8,10,10]
assert q[53].quest_item.drop_chance==q[56].quest_item.drop_chance==0.15
m=validate_story_hierarchy_metadata();assert m["production_quest_count"]==60 and m["metadata_quest_count"]==60 and m["quest_numbers"]==tuple(range(1,61))
print("PASS: Stage 19.29.2")
