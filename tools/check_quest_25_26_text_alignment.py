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
assert q25.description == 'Голова Найманців просить знову розчистити околиці старого мосту, щоб безпечно продовжити пошуки спорядження зниклого патруля.'
assert STORY_QUEST_TEXT[q25.quest_id]["acceptance_text"] == 'Якщо патруль ішов за великими вовчими слідами, сутичка могла статися біля старого мосту. Але місцевість знову заполонили небезпечні істоти. Розчисти околиці, щоб ми могли безпечно продовжити пошуки слідів патруля.'
assert q26.quest_type.value == "QUEST_ITEM"
assert q26.description == 'Після зачистки старого мосту Голова Найманців просить уважно обшукати місцевість та знайти спорядження, яке могло належати зниклому патрулю.'
assert STORY_QUEST_TEXT[q26.quest_id]["acceptance_text"] == 'Тепер біля старого мосту стало безпечніше. Повернися туди й уважно оглянь землю, каміння та зарості. Шукай уламки спорядження або інший доказ, який допоможе відновити перебіг сутички.'
assert q26.quest_item is not None and q26.quest_item.drop_chance == 0.15
assert q26.quest_item.consume_on_completion is False
assert "Шукай уламки щита або зброї" not in STORY_QUEST_TEXT[q25.quest_id]["acceptance_text"]
assert "перемогти 10" in q25.objective_text.lower()
print("QUEST 25-26 TEXT ALIGNMENT: PASS")
