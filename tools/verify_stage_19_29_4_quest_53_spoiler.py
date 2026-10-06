#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT
qid = "dark_forest_053_not_a_random_patrol"
quest = STORY_QUEST_REGISTRY[qid]
text = STORY_QUEST_TEXT[qid]
assert quest.number == 53 and quest.quest_type.value == "TALK"
assert text["acceptance_text"] == 'Розвідники повернулися зі старого шляху. Напади припинилися одразу після того, як ти відтіснив передові загони, але гобліни не розбіглися. Вони відійшли до лісу й зайняли нові позиції.\n\nНа деревах уздовж стежки розвідники помітили зарубки, а між камінням були розкладені зв’язки сухих гілок. Це не випадкові сліди. Так гобліни позначають контрольовану територію й попереджають один одного про чужинців.'
assert text["completion_text"] == 'Голова Найманців завершує доповідь: зарубки й сигнальні зв’язки підтверджують, що гоблінські дозори координують дії та контролюють прикордонний шлях.'
for phrase in ('покинутого сторожового вогнища', 'Знайди його під час полювання', 'принесеш доказ', 'точний опис місця'):
    assert phrase not in text["acceptance_text"]
    assert phrase not in text["completion_text"]
candidate = json.loads((ROOT / 'Квести/ROM_квести_Темний_Бір_candidate.json').read_text(encoding="utf-8-sig"))
q53 = next(item for item in candidate["quests"] if item["number"] == 53)
assert q53["acceptance_text"] == text["acceptance_text"]
assert q53["completion_text"] == text["completion_text"]
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values()) == tuple(range(1, 61))
print("PASS: Stage 19.29.4 quest 53 spoiler removed")
