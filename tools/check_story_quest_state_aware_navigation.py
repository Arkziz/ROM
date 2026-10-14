#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DB-free production-registry matrix for state-aware journal navigation."""
import ast
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
source_path=ROOT/"handlers/story_quests.py"
source=source_path.read_text(encoding="utf-8")
tree=ast.parse(source)
func=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="resolve_story_quest_journal_navigation"]
assert len(func)==1
from data.story_quest_definitions import QuestType
from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_location_presentation import resolve_story_quest_location_name
namespace={"QuestType":QuestType,"resolve_story_quest_location_name":resolve_story_quest_location_name}
exec(compile(ast.Module(body=func,type_ignores=[]),str(source_path),"exec"),namespace)
resolve=namespace["resolve_story_quest_journal_navigation"]
quests=sorted(STORY_QUEST_REGISTRY.values(),key=lambda q:q.number)
assert [q.number for q in quests]==list(range(1,51))
assert not hasattr(QuestType,"KILL")
assert {q.quest_type for q in quests}=={QuestType.TALK,QuestType.KILL_REGION,QuestType.QUEST_ITEM,QuestType.TURN_IN,QuestType.BOSS}
counts={"AVAILABLE":0,"ACTIVE_INCOMPLETE":0,"ACTIVE_READY":0,"COMPLETED":0}
for quest in quests:
    target=max(1,int(quest.target_quantity))
    available=resolve(quest,"AVAILABLE",0)
    assert available is not None and available[0]=="🧭 Де прийняти:" and available[1]
    counts["AVAILABLE"]+=1
    assert resolve(quest,"COMPLETED",target) is None
    assert resolve(quest,"SKIPPED",target) is None
    assert resolve(quest,"LOCKED",0) is None
    counts["COMPLETED"]+=1
    if quest.quest_type not in {QuestType.TALK,QuestType.TURN_IN}:
        incomplete=resolve(quest,"ACTIVE",0)
        assert incomplete is not None
        if quest.quest_type is QuestType.QUEST_ITEM:
            assert incomplete[0]=="🧭 Де шукати:" and "Полювання" in incomplete[1]
        elif quest.quest_type is QuestType.BOSS:
            assert incomplete[0]=="🧭 Як викликати:" and "Роззирнутися" in incomplete[1]
        elif quest.quest_type is QuestType.KILL_REGION:
            assert incomplete[0]=="🧭 Де виконувати:" and "Полювання" in incomplete[1]
        counts["ACTIVE_INCOMPLETE"]+=1
    ready=resolve(quest,"ACTIVE",target)
    assert ready is not None and ready[1]
    if quest.quest_type is QuestType.TALK:assert ready[0]=="🧭 З ким поговорити:"
    elif quest.quest_type in {QuestType.TURN_IN,QuestType.QUEST_ITEM}:assert ready[0]=="🧭 Кому передати:"
    else:assert ready[0]=="🧭 Кому доповісти:"
    counts["ACTIVE_READY"]+=1
# Quest 23 must use authoritative trader ownership, not stale next_step_hint.
q23=next(q for q in quests if q.number==23)
q23_ready=resolve(q23,"ACTIVE",1)
assert "Торгов" in q23_ready[1] and "Голова Найманців" not in q23_ready[1]
# Production builder must call the resolver and stop rendering static route hints.
builder=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_production_story_quest_detail")
builder_text=ast.get_source_segment(source,builder)
assert "resolve_story_quest_journal_navigation(quest, status, progress)" in builder_text
assert "navigation.next_step_hint" not in builder_text
assert "navigation.objective_hint" not in builder_text
assert counts=={"AVAILABLE":50,"ACTIVE_INCOMPLETE":27,"ACTIVE_READY":50,"COMPLETED":50}
print("STORY QUEST STATE-AWARE NAVIGATION: PASS")
