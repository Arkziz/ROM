#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from systems import character_system as cs

source = (ROOT / "systems/character_system.py").read_text(encoding="utf-8")
ast.parse(source)
assert source.count("ROM 17.12.1 CHARACTER NAME VALIDATION") == 1
assert "import unicodedata" in source
assert 'unicodedata.normalize("NFC"' in source
assert "any(char.isalpha() for char in value)" in source
assert "NAME_PATTERN.fullmatch(value)" not in source
assert cs.NAME_MIN_LENGTH == 2
assert cs.NAME_MAX_LENGTH == 24

# Fixtures are technical character-category combinations, not suggested names.
latin = "A" + "b"
cyrillic = "А" + "б"
greek = "Α" + "β"
cjk = "名" + "字"
letter_digit = "A" + "7"
letter_space = "A" + " " + "b"
letter_hyphen = "A" + "-" + "b"
letter_apostrophe = "A" + "'" + "b"
letter_emoji = "A" + "🙂"

for value in (
    latin, cyrillic, greek, cjk, letter_digit, letter_space,
    letter_hyphen, letter_apostrophe, letter_emoji,
):
    valid, message = cs.validate_character_name(value)
    assert valid, (value.encode("unicode_escape"), message)

for value in ("", "   ", "A", "12", "🙂🙂", "--", "_!", "12🙂"):
    valid, _message = cs.validate_character_name(value)
    assert not valid, value.encode("unicode_escape")

valid, message = cs.validate_character_name("A" * 25)
assert not valid and "24" in message
valid, message = cs.validate_character_name("12🙂")
assert not valid and "хоча б одну літеру" in message

# Existing whitespace behavior remains unchanged.
assert cs.normalize_character_name("  A   b  ") == "A b"
assert cs.normalize_character_name("A\tb") == "A b"

# NFC normalization is applied before storage/comparison.
decomposed = "A" + "\u0301"
normalized = cs.normalize_character_name(decomposed)
assert normalized == unicodedata.normalize("NFC", decomposed)
assert unicodedata.is_normalized("NFC", normalized)

# Uniqueness implementation remains normalization + casefold based.
assert ".casefold()" in source
assert "normalize_character_name(existing).casefold()" in source
print("[PASS] Stage 17.12.1 Unicode character-name validation contract")
