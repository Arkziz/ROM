#!/usr/bin/env python3
"""Maintained structural and isolated check for the KILL_REGION victory hook."""
from __future__ import annotations
import ast, importlib.util, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType, StoryQuestDefinition
from systems.story_quest_combat_progress_system import process_region_kill_story_progress
from systems.story_quest_system import accept_story_quest, build_story_quest_registry


def source_function(path,name):
    src=(ROOT/path).read_text(encoding="utf-8-sig"); tree=ast.parse(src)
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return src,ast.get_source_segment(src,nodes[0])


def schema(connection):
    path=ROOT/"migrations/053_story_quest_persistence_schema.py"
    spec=importlib.util.spec_from_file_location("migration_053_region_kill",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); module.up(connection)


def main():
    assert len(STORY_QUEST_REGISTRY)==0
    combat_src, victory=source_function("handlers/combat.py","process_victory")
    assert victory.count("process_region_kill_story_progress(")==1
    positions=[victory.index(token) for token in (
        "claim_pve_terminal", "process_victory_reward", "process_contract_progress_on_kill",
        "process_daily_quest_progress_on_kill", "process_region_kill_story_progress",
        "build_victory_text",
    )]
    assert positions==sorted(positions)
    assert "mob.get(\"id\")" not in victory and "mob.get('id')" not in victory

    q=StoryQuestDefinition(
        quest_id="fixture_region", number=1, title="Fixture",
        quest_type=QuestType.KILL_REGION, location_id="start_path",
        unlock_level=1, previous_quest_id=None, giver_npc_id="bartender",
        turn_in_npc_id="bartender", description="fixture",
        objective_text="fixture", target_quantity=2,
    )
    registry=build_story_quest_registry(((q,),))
    db=sqlite3.connect(":memory:"); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)")
    schema(db); db.execute("INSERT INTO users(user_id) VALUES(1)"); db.commit()
    accept_story_quest(db,registry=registry,user_id=1,quest_id=q.quest_id,player_level=1)
    a=process_region_kill_story_progress(user_id=1,location_id="start_path",registry=registry,connection=db)
    b=process_region_kill_story_progress(user_id=1,location_id="wrong",registry=registry,connection=db)
    c=process_region_kill_story_progress(user_id=1,location_id="start_path",registry=registry,connection=db)
    d=process_region_kill_story_progress(user_id=1,location_id="start_path",registry=registry,connection=db)
    assert a["advanced"]==1 and a["progress"]==1
    assert b=={"advanced":0,"reason":"location_mismatch"}
    assert c["advanced"]==1 and c["objective_complete"]
    assert d["advanced"]==0 and d["progress"]==2
    assert db.execute("SELECT progress FROM user_story_quests WHERE user_id=1").fetchone()[0]==2
    db.close()
    print("[PASS] KILL_REGION canonical victory progress hook")
if __name__=="__main__": main()
