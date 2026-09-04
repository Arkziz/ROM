#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.guild_system import normalize_guild_tag,validate_guild_tag_contract
valid=("DLC","abc","ДЛК","ЇЖА","ЄДН","ІГР","ҐАР"," DLC ")
invalid=("A","AB","ABCD","ДЛ","ДЛКИ","DL1","D-L","D_L","D L","⚔️D","[D]","ЁЖА","ЫВА","ЭРА","ЪЬЬ")
for value in valid:assert validate_guild_tag_contract(value)["success"],value
for value in invalid:assert not validate_guild_tag_contract(value)["success"],value
assert normalize_guild_tag(" dlc ")=="DLC"
s=(ROOT/"systems/guild_system.py").read_text(encoding="utf-8-sig");t=ast.parse(s)
assert len([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="validate_guild_create_input"])==1
assert len([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="validate_guild_tag_contract"])==1
h=(ROOT/"handlers/guild.py").read_text(encoding="utf-8-sig")
assert "від 2 до 5 символів" not in h and "тільки літери та цифри" not in h
assert "рівно 3 літери" in h and "українські або латинські літери" in h
print("PASS: exact three-letter policy, prohibited symbols, UI parity and validator consolidation")
