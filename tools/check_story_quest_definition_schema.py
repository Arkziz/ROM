#!/usr/bin/env python3
"""Maintained check for the canonical story-quest definition schema."""
from __future__ import annotations
import sys
from dataclasses import replace
from pathlib import Path

# A directly executed script starts with ROM/tools on sys.path. Add ROM explicitly
# so PowerShell, patch, CI and manual invocation all use the same import contract.
ROM_ROOT=Path(__file__).resolve().parents[1]
if str(ROM_ROOT) not in sys.path: sys.path.insert(0,str(ROM_ROOT))

from data.story_quest_definitions import DerivedQuestStatus, PersistentQuestStatus, QuestDefinitionError, QuestType, SCHEMA_FIXTURES, derive_story_quest_status, validate_story_quest_definition, validate_story_quest_pack

def invalid(quest):
    try: validate_story_quest_definition(quest)
    except QuestDefinitionError: return
    raise AssertionError('invalid fixture accepted')

def main():
    assert len(validate_story_quest_pack(SCHEMA_FIXTURES))==5
    assert {q.quest_type for q in SCHEMA_FIXTURES}==set(QuestType)
    invalid(replace(SCHEMA_FIXTURES[0],target_quantity=0))
    invalid(replace(SCHEMA_FIXTURES[2],quest_item=None))
    invalid(replace(SCHEMA_FIXTURES[4],boss_key=None))
    assert derive_story_quest_status(persistent_status=None,player_level=1,unlock_level=1,predecessor_completed=True,another_active_quest=False) is DerivedQuestStatus.AVAILABLE
    assert derive_story_quest_status(persistent_status=None,player_level=1,unlock_level=2,predecessor_completed=True,another_active_quest=False) is DerivedQuestStatus.LOCKED
    assert derive_story_quest_status(persistent_status=PersistentQuestStatus.COMPLETED,player_level=1,unlock_level=99,predecessor_completed=False,another_active_quest=True) is PersistentQuestStatus.COMPLETED
    print('[PASS] story quest definition schema')
if __name__=='__main__': main()
