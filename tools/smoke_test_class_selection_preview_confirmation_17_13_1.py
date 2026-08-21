#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
start_path = ROOT / "handlers/start.py"
character_path = ROOT / "systems/character_system.py"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

before = sha256(DB)
start = start_path.read_text(encoding="utf-8")
character = character_path.read_text(encoding="utf-8")
ast.parse(start); ast.parse(character)
assert start.count("ROM 17.13.1 CLASS SELECTION PREVIEW CONFIRMATION") == 1
assert character.count("ROM 17.13.1 CLASS SELECTION PREVIEW CONFIRMATION") == 1
assert 'callback_data=f"class_preview:{mode}:{class_key}"' in start
assert 'callback_data=f"class_confirm:{mode}:{class_key}"' in start
assert 'callback_data=f"class_back:{mode}"' in start
assert 'text="✅ Обрати клас"' in start
assert 'text="⬅️ Назад до вибору"' in start
assert "from handlers.combat import CLASS_SKILLS_V1" in start
assert "bot.edit_message_text(" in start
assert "def confirm_initial_character_class_17_13_1" in character
assert "def confirm_character_class_change_17_13_1" in character
assert 'db.conn.execute("BEGIN IMMEDIATE")' in character
assert "class_change_available=class_change_available-1" in character
assert "db.conn.rollback()" in character
assert "set_character_class(user_id, class_key)" not in start[start.rfind("# Stage 17.13.1"):]
assert sha256(DB) == before
print("[PASS] Stage 17.13.1 class preview/confirmation contract")
