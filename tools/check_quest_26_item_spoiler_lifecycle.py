#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT

by = {q.number: q for q in STORY_QUEST_REGISTRY.values()}
q25, q26 = by[25], by[26]
assert q25.quest_type.value == "KILL_REGION" and q25.target_quantity == 10
assert STORY_QUEST_TEXT[q25.quest_id]["completion_text"] == 'Після зачистки околиць біля кам’яної опори мосту стали помітні глибокі борозни та сліди давньої сутички. Тепер місцевість можна ретельно обшукати.'
assert q26.quest_type.value == "QUEST_ITEM"
assert q26.objective_text == 'Обшукати околиці старого мосту та знайти доказ, пов’язаний зі зниклим патрулем.'
assert q26.quest_item is not None and q26.quest_item.drop_chance == 0.15
assert q26.quest_item.consume_on_completion is False
fields = (
    STORY_QUEST_TEXT[q25.quest_id]["completion_text"],
    q26.description,
    STORY_QUEST_TEXT[q26.quest_id]["acceptance_text"],
    q26.objective_text,
)
for text in fields:
    lowered = text.lower()
    assert not any(phrase in lowered for phrase in ('пошкоджений щит', 'щит вартового', 'частина пошкодженого щита'))
drop = STORY_QUEST_TEXT[q26.quest_id]["drop_message"]
assert q26.quest_item.display_name.lower() in drop.lower()
source = (ROOT / "data/story_quests/start_path_21_30.py").read_text(encoding="utf-8")
assert len(source.splitlines()) > 100
assert max(len(line) for line in source.splitlines()) <= 240
print("QUEST 26 ITEM SPOILER LIFECYCLE: PASS")
