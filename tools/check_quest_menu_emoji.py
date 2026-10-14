#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression contract for the Stage 19.28.11 quest-menu emoji."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
story = (ROOT / "handlers/story_quests.py").read_text(encoding="utf-8")
keyboards = (ROOT / "keyboards.py").read_text(encoding="utf-8")

assert 'STORY_QUEST_BUTTON_TEXT = "📖 Квести"' in story
assert 'STORY_QUEST_BUTTON_TEXT = "📜 Квести"' not in story
assert 'kb.row("🎒 Інвентар", "📖 Квести")' in keyboards
assert 'kb.row("🎒 Інвентар", "📜 Квести")' not in keyboards

# Preserve semantically distinct scroll uses and internal section navigation.
assert '📜 Історія' in keyboards
assert '🔙 Квести розділу' in story
assert keyboards.count('📜 Історія') == 1

# Exact user-facing quest entry label occurs once in each authoritative owner.
assert story.count("📖 Квести") == 1
assert keyboards.count("📖 Квести") == 1
print("QUEST MENU EMOJI: PASS")
