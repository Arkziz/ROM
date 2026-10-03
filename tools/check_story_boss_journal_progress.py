#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DB-free synthetic snapshots for story BOSS journal progress."""
import ast
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
source_path=ROOT/"handlers/story_quests.py"
source=source_path.read_text(encoding="utf-8")
tree=ast.parse(source)
helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_should_show_story_quest_progress"]
assert len(helpers)==1
QUEST_ITEM=object();BOSS=object();KILL=object()
namespace={"QuestType":SimpleNamespace(QUEST_ITEM=QUEST_ITEM,BOSS=BOSS)}
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(source_path),"exec"),namespace)
show=namespace["_should_show_story_quest_progress"]
def quest(kind,target):return SimpleNamespace(quest_type=kind,target_quantity=target)
# Synthetic lifecycle snapshots.
assert show("ACTIVE",quest(BOSS,1)) is True       # active boss 0/1 and 1/1
assert show("COMPLETED",quest(BOSS,1)) is False  # completed history stays unchanged
assert show("AVAILABLE",quest(BOSS,1)) is False
assert show("ACTIVE",quest(QUEST_ITEM,1)) is True
assert show("ACTIVE",quest(KILL,1)) is False
assert show("ACTIVE",quest(KILL,10)) is True
builders=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_production_story_quest_detail"]
assert len(builders)==1
text=ast.get_source_segment(source,builders[0])
assert "_should_show_story_quest_progress(status, quest)" in text
assert 'quest.quest_type is QuestType.BOSS' in text
assert '"✅ Ватажка переможено."' in text
assert '"Повернися до Голови Найманців із доповіддю."' in text
assert text.index('"📈 Прогрес:"') < text.index('"✅ Ватажка переможено."')
print("STORY BOSS JOURNAL PROGRESS: PASS")
