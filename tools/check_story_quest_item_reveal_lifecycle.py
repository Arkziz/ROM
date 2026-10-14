#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT

by = {q.number: q for q in STORY_QUEST_REGISTRY.values()}
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values()) == tuple(range(1, 31))
for n, target in {22: 8, 25: 10, 28: 10}.items():
    assert by[n].quest_type.value == "KILL_REGION"
    assert by[n].target_quantity == target
for n in (23, 26, 29):
    q = by[n]
    assert q.quest_type.value == "QUEST_ITEM"
    assert q.quest_item is not None
    assert q.quest_item.drop_chance == 0.15
    assert q.quest_item.consume_on_completion is False
    display = q.quest_item.display_name
    tokens = {display.casefold()} | {w for w in display.casefold().replace("-", " ").split() if len(w) >= 5}
    fields = (
        STORY_QUEST_TEXT[by[n - 1].quest_id]["completion_text"],
        q.description,
        STORY_QUEST_TEXT[q.quest_id]["acceptance_text"],
        q.objective_text,
    )
    for text in fields:
        lowered = text.casefold()
        assert not any(token in lowered for token in tokens)
    assert display.casefold() in STORY_QUEST_TEXT[q.quest_id]["drop_message"].casefold()
q30 = by[30]
assert q30.quest_type.value == "TURN_IN"
assert len(q30.required_quest_items) == 3
assert all(item.consume is True for item in q30.required_quest_items)
source = (ROOT / "data/story_quests/start_path_21_30.py").read_text(encoding="utf-8")
assert len(source.splitlines()) > 100
assert max(len(line) for line in source.splitlines()) <= 240
print("QUEST ITEM REVEAL LIFECYCLE 23/26/29: PASS")
