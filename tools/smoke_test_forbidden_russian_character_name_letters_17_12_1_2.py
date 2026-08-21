#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
SOURCE = ROOT / "systems/character_system.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


before = sha256(DB)
source = SOURCE.read_text(encoding="utf-8")
ast.parse(source)
assert source.count("ROM 17.12.1.2 FORBIDDEN NON-UKRAINIAN CYRILLIC NAME LETTERS") == 1
assert 'FORBIDDEN_NON_UKRAINIAN_CYRILLIC_LETTERS = frozenset("ёЁъЪыЫэЭ")' in source
assert "any(char in FORBIDDEN_NON_UKRAINIAN_CYRILLIC_LETTERS for char in value)" in source
assert "Ім’я містить літери, яких немає в українській абетці." in source

from systems import character_system as cs

for forbidden in "ёЁъЪыЫэЭ":
    valid, message = cs.validate_character_name("А" + forbidden)
    assert not valid, forbidden.encode("unicode_escape")
    assert message == "Ім’я містить літери, яких немає в українській абетці."

for allowed in ("Іі", "Її", "Єє", "Ґґ", "Аб", "A🙂", "Αβ", "名字"):
    valid, message = cs.validate_character_name(allowed)
    assert valid, (allowed.encode("unicode_escape"), message)

for invalid in ("12", "🙂🙂", "--"):
    valid, _message = cs.validate_character_name(invalid)
    assert not valid

assert cs.NAME_MIN_LENGTH == 2
assert cs.NAME_MAX_LENGTH == 24
assert 'unicodedata.normalize("NFC"' in source
assert ".casefold()" in source
assert sha256(DB) == before
print("[PASS] Stage 17.12.1.2 non-Ukrainian Cyrillic letter restriction")
