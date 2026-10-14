#!/usr/bin/env python3
"""Maintained isolated and structural check for guaranteed story boss call."""
from __future__ import annotations
import ast,importlib.util,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_definitions import QuestType,StoryQuestDefinition
from systems.story_quest_boss_call_system import BOSS_CALL_BUTTON,get_active_story_boss_call
from systems.story_quest_system import accept_story_quest,build_story_quest_registry

def schema(c):
 p=ROOT/"migrations/053_story_quest_persistence_schema.py";s=importlib.util.spec_from_file_location("m053call",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.up(c)
def fn(path,name):
 src=(ROOT/path).read_text(encoding="utf-8-sig");t=ast.parse(src);nodes=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name==name];assert len(nodes)==1,(name,len(nodes));return ast.get_source_segment(src,nodes[0])
def main():
 q=StoryQuestDefinition(quest_id="boss",number=1,title="Boss",quest_type=QuestType.BOSS,location_id="start_path",unlock_level=1,previous_quest_id=None,giver_npc_id="mercenary_head",turn_in_npc_id=None,description="x",objective_text="x",boss_key="pack_leader")
 reg=build_story_quest_registry(((q,),));c=sqlite3.connect(":memory:");c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");c.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)");schema(c);c.execute("INSERT INTO users VALUES(1)");c.commit()
 assert not get_active_story_boss_call(user_id=1,current_location_id="start_path",registry=reg,connection=c)["allowed"]
 accept_story_quest(c,registry=reg,user_id=1,quest_id="boss",player_level=1)
 assert get_active_story_boss_call(user_id=1,current_location_id="start_path",registry=reg,connection=c)["allowed"]
 assert not get_active_story_boss_call(user_id=1,current_location_id="dark_forest",registry=reg,connection=c)["allowed"]
 c.execute("UPDATE user_story_quests SET status='COMPLETED',reward_claimed=1,progress=1 WHERE user_id=1");c.commit()
 assert get_active_story_boss_call(user_id=1,current_location_id="start_path",registry=reg,connection=c)["reason"]=="no_active_quest"
 c.close()
 kb=(ROOT/"keyboards.py").read_text(encoding="utf-8-sig");city=(ROOT/"handlers/city.py").read_text(encoding="utf-8-sig");combat=(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")
 # The button label is imported at runtime, so validate the identifier and
 # eligibility owner reference rather than searching for the literal emoji text.
 assert "BOSS_CALL_BUTTON" in kb and "get_active_story_boss_call" in kb
 assert "mercenary_head_kb(message.from_user.id)" in city
 handler=fn("handlers/combat.py","call_active_story_boss")
 for token in ("get_active_story_boss_call","get_active_pve_encounter","build_location_boss","begin_pve_encounter","build_combat_inline_kb"):
  assert token in handler,token
 assert handler.index("get_active_story_boss_call") < handler.index("build_location_boss")
 assert "process_rng_boss_story_completion" not in handler
 print("[PASS] guarded one-success story boss call")
if __name__=="__main__":main()
