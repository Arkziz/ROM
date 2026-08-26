import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
for rel in ("systems/guild_system.py","db_modules/systems_wrappers.py","db_modules/__init__.py","handlers/guild.py"):ast.parse((R/rel).read_text(encoding="utf-8"),filename=rel)
s=(R/"systems/guild_system.py").read_text(encoding="utf-8");t=ast.parse(s)
assert "GUILD_CREATE_COST_GOLD = 100.0" in s and "DEFAULT_GUILD_MEMBER_LIMIT = 10" in s
assert len([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="create_guild"])==1
import db
assert callable(db.create_guild) and callable(db.get_guild_creation_terms)
h=(R/"handlers/guild.py").read_text(encoding="utf-8")
assert "get_guild_creation_terms" in h and "Вартість:" in h and "Початковий ліміт:" in h
print("[PASS] Stage 17.23.1 static paid creation contract")
