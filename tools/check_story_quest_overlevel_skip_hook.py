#!/usr/bin/env python3
"""Maintained isolated check for post-reward overlevel story quest skipping."""
from __future__ import annotations
import ast, importlib.util, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_definitions import QuestItemDefinition, QuestType, StoryQuestDefinition
from systems.story_quest_overlevel_system import process_overlevel_story_quest_skip
from systems.story_quest_system import accept_story_quest, build_story_quest_registry, collect_active_quest_item


def function(path,name):
    source=(ROOT/path).read_text(encoding="utf-8-sig"); tree=ast.parse(source)
    nodes=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return source,ast.get_source_segment(source,nodes[0])


def schema(connection):
    path=ROOT/"migrations/053_story_quest_persistence_schema.py"
    spec=importlib.util.spec_from_file_location("migration_053_overlevel",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); module.up(connection)


def fixture_registry():
    quest=StoryQuestDefinition(
        quest_id="fixture_overlevel",number=1,title="Fixture",
        quest_type=QuestType.QUEST_ITEM,location_id="start_path",unlock_level=1,
        previous_quest_id=None,giver_npc_id="bartender",turn_in_npc_id="bartender",
        description="fixture",objective_text="fixture",target_quantity=2,
        quest_item=QuestItemDefinition("fixture_item","Fixture Item",2,1.0),
    )
    return quest,build_story_quest_registry(((quest,),))


def new_db(user_id):
    connection=sqlite3.connect(":memory:"); connection.row_factory=sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY, level INTEGER NOT NULL DEFAULT 1)")
    schema(connection); connection.execute("INSERT INTO users(user_id,level) VALUES(?,1)",(user_id,)); connection.commit()
    return connection


def main():
    combat_source,victory=function("handlers/combat.py","process_victory")
    assert victory.count("process_overlevel_story_quest_skip(")==1
    ordered=("process_victory_reward","process_region_kill_story_progress",
             "process_story_quest_item_drop","process_overlevel_story_quest_skip",
             "build_victory_text")
    positions=[victory.index(token) for token in ordered]
    assert positions==sorted(positions)
    assert 'reward.get("exp_result")' in victory
    assert 'get_player_level(user_id)' in victory

    quest,registry=fixture_registry(); db=new_db(1)
    accept_story_quest(db,registry=registry,user_id=1,quest_id=quest.quest_id,player_level=1)
    collect_active_quest_item(db,registry=registry,user_id=1,location_id="start_path",item_key="fixture_item")
    not_skipped=process_overlevel_story_quest_skip(user_id=1,current_level=5,registry=registry,connection=db,location_max_levels={"start_path":5})
    assert not_skipped is None
    skipped=process_overlevel_story_quest_skip(user_id=1,current_level=6,registry=registry,connection=db,location_max_levels={"start_path":5})
    assert skipped["status"]=="SKIPPED" and skipped["reward_claimed"]==0
    assert db.execute("SELECT COUNT(*) FROM user_story_quest_items WHERE user_id=1").fetchone()[0]==0
    db.close()

    quest2,registry2=fixture_registry(); db2=new_db(2)
    accept_story_quest(db2,registry=registry2,user_id=2,quest_id=quest2.quest_id,player_level=1)
    db2.execute("UPDATE user_story_quests SET status='COMPLETED', reward_claimed=1 WHERE user_id=2")
    db2.commit()
    assert process_overlevel_story_quest_skip(user_id=2,current_level=6,registry=registry2,connection=db2,location_max_levels={"start_path":5}) is None
    row=db2.execute("SELECT status,reward_claimed FROM user_story_quests WHERE user_id=2").fetchone()
    assert tuple(row)==("COMPLETED",1)
    db2.close()
    print("[PASS] post-reward overlevel story quest skip")
if __name__=="__main__": main()
