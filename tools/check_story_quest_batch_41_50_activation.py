from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT
from data.story_quest_hierarchy import ordered_story_sections, get_story_section_for_quest_number
rows=tuple(STORY_QUEST_REGISTRY.values())
assert tuple(q.number for q in rows)==tuple(range(1,51))
assert 51 not in tuple(q.number for q in rows)
for number in range(41,51):
    q=next(q for q in rows if q.number==number)
    assert q.location_id=="start_path" and q.unlock_level==5
    text=STORY_QUEST_TEXT[q.quest_id]
    assert set(text)=={"acceptance_text","completion_text","progress_text","drop_message"}
    assert text["acceptance_text"] and text["completion_text"] and text["progress_text"]
sections=ordered_story_sections("start_path")
assert tuple(s.quest_numbers for s in sections)==(
    tuple(range(1,11)),tuple(range(11,21)),tuple(range(21,31)),tuple(range(31,41)),tuple(range(41,51))
)
sec=get_story_section_for_quest_number(49)
assert sec.section_id=="start_path_05" and sec.title=="Вирішальний похід" and sec.required_level==5
by={q.number:q for q in rows}
selected=tuple(by[n] for n in range(41,51))
assert all(q.navigation is not None for q in selected)
assert all(q.navigation.location_id == q.location_id for q in selected)
assert all(q.navigation.giver_npc_id == q.giver_npc_id for q in selected)
assert all(q.navigation.turn_in_npc_id == q.turn_in_npc_id for q in selected)
assert [by[n].target_quantity for n in (42,45,48)]==[15,15,10]
for source_no,turn_no in ((43,44),(46,47)):
    src,turn=by[source_no],by[turn_no]
    assert src.quest_item is not None and src.quest_item.drop_chance==0.15
    assert src.quest_item.consume_on_completion is False
    assert len(turn.required_quest_items)==1
    assert turn.required_quest_items[0].item_key==src.quest_item.item_key
    assert turn.required_quest_items[0].consume is True
    assert turn.quest_item_consumption=="atomic_exact_once"
boss=by[49]
assert boss.quest_type.value=="BOSS" and boss.target_quantity==1 and boss.boss_key=='pack_leader'
assert boss.giver_npc_id=="mercenary_head" and (boss.turn_in_npc_id or boss.giver_npc_id)=="mercenary_head"
assert boss.reward.exp==95 and round(boss.reward.gold,2)==2.15
# Import success proves authoring-only reward metadata did not leak into RewardDefinition.
assert all(not hasattr(quest.reward, "formula") for quest in selected)
assert all(quest.reward.item_keys == () for quest in selected)
final=by[50]
assert final.quest_type.value=="TURN_IN" and not final.required_quest_items
assert final.giver_npc_id=="elder" and (final.turn_in_npc_id or final.giver_npc_id)=="elder"
print("STORY QUEST BATCH 41-50 ACTIVATION: PASS")
