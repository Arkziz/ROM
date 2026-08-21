#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
SOURCE_PATH = ROOT / "handlers/start.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


before = sha256(DB)
source = SOURCE_PATH.read_text(encoding="utf-8")
tree = ast.parse(source)
assert source.count("ROM 17.13.1.2 CLASS SKILL PREVIEW SPACING") == 1
assert "for index, skill in enumerate(skills):" in source
assert 'if index:\n            text += "\\n"' in source
assert source.count('callback_data=f"class_confirm:{mode}:{class_key}"') == 1
assert source.count('callback_data=f"class_back:{mode}"') == 1

from handlers import start

class_key = next(iter(start.CLASS_CONFIGS))
text = start.build_class_preview_text_17_13_1(0, "register", class_key)
from handlers.combat import CLASS_SKILLS_V1
skills = CLASS_SKILLS_V1[class_key]
assert len(skills) == 3
for skill in skills:
    assert skill["name"] in text
for left, right in zip(skills, skills[1:]):
    left_cooldown = int(left.get("cooldown", 0) or 0)
    expected = f"Перезарядка: {left_cooldown} ход.\n\n• {right['name']}"
    assert expected in text, expected
assert sha256(DB) == before
print("[PASS] Stage 17.13.1.2 blank line between class preview skills")
