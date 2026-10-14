#!/usr/bin/env python3
"""Maintained structural contract check for the story reward adapter."""
from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.story_quest_reward_system import build_story_quest_reward_adapter


def body(path,name):
    src=(ROOT/path).read_text(encoding="utf-8-sig"); tree=ast.parse(src)
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1, (name,len(nodes))
    return ast.get_source_segment(src,nodes[0])


def main():
    exp=body("systems/player_system.py","apply_exp_in_transaction")
    gold=body("systems/player_system.py","apply_gold_in_transaction")
    adapter=body("systems/story_quest_reward_system.py","build_story_quest_reward_adapter")
    for text in (exp,gold,adapter):
        assert "commit(" not in text and "rollback(" not in text
        assert "BEGIN IMMEDIATE" not in text
    assert "connection is not db.conn" in exp and "connection is not db.conn" in gold
    assert "apply_level_up_rewards_in_transaction" in exp
    assert "get_max_hp" in exp and "free_attribute_points" in exp
    assert "apply_exp_in_transaction" in adapter and "apply_gold_in_transaction" in adapter
    assert "send_message" not in adapter and "telebot" not in adapter
    try: build_story_quest_reward_adapter(exp=-1,gold=0)
    except ValueError: pass
    else: raise AssertionError("negative reward accepted")
    print("[PASS] story quest same-connection reward adapter")
if __name__=="__main__": main()
