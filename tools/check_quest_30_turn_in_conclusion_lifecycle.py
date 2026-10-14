#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT

by = {q.number: q for q in STORY_QUEST_REGISTRY.values()}
q30 = by[30]
assert q30.quest_type.value == "TURN_IN"
assert q30.description == 'Голова Найманців просить принести всі три знайдені докази, щоб зіставити їх і відновити перебіг нападу на патруль.'
assert q30.objective_text == 'Показати Голові Найманців усі три зібрані докази.'
assert STORY_QUEST_TEXT[q30.quest_id]["acceptance_text"] == 'Принеси перстень, пошкоджений щит і подертий клапоть плаща. Голова Найманців зіставить докази та спробує відновити шлях зниклого патруля.'
assert STORY_QUEST_TEXT[q30.quest_id]["completion_text"] == 'Голова Найманців уважно зіставляє три докази. Перстень підтверджує, що патруль дістався печер. Подряпини на щиті залишили великі кігті, а в тканині застрягла вовча шерсть. Це не схоже на випадковий напад. Зграя переслідувала вартових від мосту до печер, перекриваючи їм шлях назад. Потрібно підготувати мисливців, зміцнити спорядження та знайти лігво.'
assert len(q30.required_quest_items) == 3
assert all(item.quantity == 1 and item.consume is True for item in q30.required_quest_items)
assert q30.reward.exp == 42 and abs(q30.reward.gold - 0.65) < 1e-12
for text in (q30.description, STORY_QUEST_TEXT[q30.quest_id]["acceptance_text"], q30.objective_text):
    lowered = text.casefold()
    assert "перстень підтверджує" not in lowered
    assert "подряпини на щиті" not in lowered
    assert "зграя переслідувала" not in lowered
completion = STORY_QUEST_TEXT[q30.quest_id]["completion_text"].casefold()
assert "перстень підтверджує" in completion
assert "подряпини на щиті" in completion
assert "зграя переслідувала" in completion
runtime = (ROOT / "handlers/story_quest_npc_runtime.py").read_text(encoding="utf-8")
assert '🔍 Показати докази' not in runtime
assert '📦 Передати докази' in runtime
module = (ROOT / "data/story_quests/start_path_21_30.py").read_text(encoding="utf-8")
assert len(module.splitlines()) > 100
assert max(len(line) for line in module.splitlines()) <= 240
print("QUEST 30 TURN_IN CONCLUSION LIFECYCLE: PASS")
