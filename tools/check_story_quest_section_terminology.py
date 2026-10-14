#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast,json,sys
ROOT=Path(__file__).resolve().parents[1]
FILES=(
 ROOT/"handlers/story_quest_npc_runtime.py",
 ROOT/"data/story_quests/start_path_01_10.py",
 ROOT/"data/story_quests/start_path_11_20.py",
 ROOT/"Квести/ROM_квести_Початок_Шляху_candidate.json",
)
for path in FILES:
 text=path.read_text(encoding="utf-8")
 lowered=text.casefold()
 for term in ("глава","главу","глави","главою","главі"):
  assert term not in lowered,(path,term)
 if path.suffix==".py":compile(text,str(path),"exec")
 else:json.loads(text)
runtime=FILES[0].read_text(encoding="utf-8")
assert "📖 Наступний розділ:" in runtime
assert "ℹ️ Наступний розділ поки не активовано." in runtime
assert "✅ Розділ «Тривога на околиці» завершено." in FILES[1].read_text(encoding="utf-8")
assert "✅ Розділ «Рунічна аномалія» завершено." in FILES[2].read_text(encoding="utf-8")
candidate=FILES[3].read_text(encoding="utf-8")
assert "завершує підготовчий розділ." in candidate
assert "✅ Розділ «Вовча загроза» завершено." in candidate
# Technical guard remains authoritative and intentionally searches for the forbidden word.
hierarchy=(ROOT/"data/story_quest_hierarchy.py").read_text(encoding="utf-8")
assert 'if "глава" in section.display_title.casefold()' in hierarchy
print("STORY QUEST SECTION TERMINOLOGY: PASS")
