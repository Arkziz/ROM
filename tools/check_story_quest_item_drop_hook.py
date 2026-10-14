#!/usr/bin/env python3
"""Maintained isolated check for the QUEST_ITEM canonical victory hook."""
from __future__ import annotations
import ast, importlib.util, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestItemDefinition, QuestType, StoryQuestDefinition
from systems.story_quest_item_drop_system import process_story_quest_item_drop
from systems.story_quest_system import accept_story_quest, build_story_quest_registry


def function(path,name):
    src=(ROOT/path).read_text(encoding="utf-8-sig"); tree=ast.parse(src)
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return src,ast.get_source_segment(src,nodes[0])


def schema(connection):
    path=ROOT/"migrations/053_story_quest_persistence_schema.py"
    spec=importlib.util.spec_from_file_location("migration_053_item_drop",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); module.up(connection)


def main():
    assert len(STORY_QUEST_REGISTRY)==0
    combat_src,victory=function("handlers/combat.py","process_victory")
    assert victory.count("process_story_quest_item_drop(")==1
    ordered=("claim_pve_terminal","process_victory_reward","process_contract_progress_on_kill",
             "process_daily_quest_progress_on_kill","process_region_kill_story_progress",
             "process_story_quest_item_drop","build_victory_text")
    positions=[victory.index(token) for token in ordered]
    assert positions==sorted(positions)
    drop_src,drop_body=function("systems/story_quest_item_drop_system.py","process_story_quest_item_drop")
    # Audit executable AST only. The docstring intentionally documents that
    # ordinary inventory is excluded, so a raw substring check would be false.
    drop_tree=ast.parse(drop_body)
    executable=[]
    for node in ast.walk(drop_tree):
        if isinstance(node,(ast.Import,ast.ImportFrom,ast.Call,ast.Attribute,ast.Name)):
            executable.append(ast.get_source_segment(drop_body,node) or "")
    executable_text="\n".join(executable)
    for forbidden in ("db_modules.inventory", "bag_slots", "add_item", "mob_id", "mob.get"):
        assert forbidden not in executable_text, forbidden

    q=StoryQuestDefinition(
        quest_id="fixture_item",number=1,title="Fixture",quest_type=QuestType.QUEST_ITEM,
        location_id="start_path",unlock_level=1,previous_quest_id=None,
        giver_npc_id="bartender",turn_in_npc_id="bartender",description="fixture",
        objective_text="fixture",target_quantity=2,
        quest_item=QuestItemDefinition("fixture_shard","Fixture Shard",2,0.5),
    )
    registry=build_story_quest_registry(((q,),))
    db=sqlite3.connect(":memory:"); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)")
    schema(db); db.execute("INSERT INTO users(user_id) VALUES(1)"); db.commit()
    accept_story_quest(db,registry=registry,user_id=1,quest_id=q.quest_id,player_level=1)
    miss=process_story_quest_item_drop(user_id=1,location_id="start_path",registry=registry,connection=db,random_value=lambda:0.9)
    wrong=process_story_quest_item_drop(user_id=1,location_id="wrong",registry=registry,connection=db,random_value=lambda:0.0)
    first=process_story_quest_item_drop(user_id=1,location_id="start_path",registry=registry,connection=db,random_value=lambda:0.0)
    second=process_story_quest_item_drop(user_id=1,location_id="start_path",registry=registry,connection=db,random_value=lambda:0.0)
    capped=process_story_quest_item_drop(user_id=1,location_id="start_path",registry=registry,connection=db,random_value=lambda:0.0)
    assert miss["reason"]=="drop_missed" and miss["granted"]==0
    assert wrong=={"granted":0,"reason":"location_mismatch"}
    assert first["granted"]==1 and first["quantity"]==1
    assert second["granted"]==1 and second["quantity"]==2 and second["objective_complete"]
    assert capped["granted"]==0 and capped["reason"]=="target_reached"
    row=db.execute("SELECT quantity FROM user_story_quest_items WHERE user_id=1 AND item_key='fixture_shard'").fetchone()
    assert row[0]==2
    db.close()
    print("[PASS] QUEST_ITEM canonical victory drop hook")
if __name__=="__main__": main()
