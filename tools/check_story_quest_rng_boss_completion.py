#!/usr/bin/env python3
"""Maintained isolated check for RNG boss story quest completion."""
from __future__ import annotations
import ast, importlib.util, sqlite3, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_definitions import QuestType, RewardDefinition, StoryQuestDefinition
from systems.story_quest_boss_completion_system import process_rng_boss_story_completion
from systems.story_quest_system import accept_story_quest, build_story_quest_registry


def function(path,name):
    source=(ROOT/path).read_text(encoding="utf-8-sig"); tree=ast.parse(source)
    nodes=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return source,ast.get_source_segment(source,nodes[0])


def schema(connection):
    path=ROOT/"migrations/053_story_quest_persistence_schema.py"
    spec=importlib.util.spec_from_file_location("migration_053_boss",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); module.up(connection)


def main():
    _source,victory=function("handlers/combat.py","process_victory")
    assert victory.count("process_rng_boss_story_completion(")==1
    ordered=("claim_pve_terminal","process_victory_reward","process_rng_boss_story_completion",
             "process_contract_progress_on_kill","process_overlevel_story_quest_skip",
             "build_victory_text")
    positions=[victory.index(token) for token in ordered]
    assert positions==sorted(positions)

    completion_source,completion=function("systems/story_quest_completion_system.py","complete_active_story_quest")
    assert "objective_preparer" in completion
    assert completion.index("objective_preparer(") < completion.index("_objective_ready(")
    boss_source,boss=function("systems/story_quest_boss_completion_system.py","process_rng_boss_story_completion")
    assert "generate_mob" not in boss and "random" not in boss
    assert "boss_key_mismatch" in boss and "location_mismatch" in boss

    quest=StoryQuestDefinition(
        quest_id="fixture_boss",number=1,title="Fixture Boss",quest_type=QuestType.BOSS,
        location_id="start_path",unlock_level=1,previous_quest_id=None,
        giver_npc_id="mercenary_head",turn_in_npc_id=None,description="fixture",
        objective_text="fixture",target_quantity=1,boss_key="alpha",
        reward=RewardDefinition(exp=7,gold=3.0),
    )
    registry=build_story_quest_registry(((quest,),))
    db=sqlite3.connect(":memory:"); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("""CREATE TABLE users(
        user_id INTEGER PRIMARY KEY, level INTEGER NOT NULL DEFAULT 1,
        exp INTEGER NOT NULL DEFAULT 0, gold REAL NOT NULL DEFAULT 0,
        max_hp INTEGER NOT NULL DEFAULT 130,
        free_attribute_points INTEGER NOT NULL DEFAULT 0,
        total_attribute_points_earned INTEGER NOT NULL DEFAULT 0
    )""")
    schema(db); db.execute("INSERT INTO users(user_id) VALUES(1)"); db.commit()
    accept_story_quest(db,registry=registry,user_id=1,quest_id=quest.quest_id,player_level=1)

    # Isolate exact-once orchestration from the production player-stat owner.
    import systems.story_quest_boss_completion_system as bridge
    awards=[]
    def reward_factory(*,exp,gold):
        def adapter(*,connection,user_id,quest,idempotency_key):
            awards.append((exp,gold,idempotency_key))
            connection.execute("UPDATE users SET exp=exp+?,gold=gold+? WHERE user_id=?",(exp,gold,user_id))
            return {"exp_awarded":exp,"gold_awarded":gold}
        return adapter
    original=bridge.build_story_quest_reward_adapter; bridge.build_story_quest_reward_adapter=reward_factory
    try:
        normal=process_rng_boss_story_completion(user_id=1,mob={"is_boss":False},location_id="start_path",encounter_id=1,registry=registry,connection=db)
        wrong=process_rng_boss_story_completion(user_id=1,mob={"is_boss":True,"boss_key":"other"},location_id="start_path",encounter_id=2,registry=registry,connection=db)
        result=process_rng_boss_story_completion(user_id=1,mob={"is_boss":True,"boss_key":"alpha"},location_id="start_path",encounter_id=3,registry=registry,connection=db)
        replay=process_rng_boss_story_completion(user_id=1,mob={"is_boss":True,"boss_key":"alpha"},location_id="start_path",encounter_id=3,registry=registry,connection=db)
    finally:
        bridge.build_story_quest_reward_adapter=original
    assert normal["reason"]=="not_boss" and wrong["reason"]=="boss_key_mismatch"
    assert result["completed"] and not result["already_processed"]
    assert replay["completed"] and replay["already_processed"]
    assert replay["reason"]=="completed"
    assert len(awards)==1
    row=db.execute("SELECT status,reward_claimed,progress FROM user_story_quests WHERE user_id=1").fetchone()
    assert tuple(row)==("COMPLETED",1,1)
    wallet=db.execute("SELECT exp,gold FROM users WHERE user_id=1").fetchone()
    assert tuple(wallet)==(7,3.0)
    db.close()
    print("[PASS] RNG boss exact-once story quest completion")
if __name__=="__main__": main()
