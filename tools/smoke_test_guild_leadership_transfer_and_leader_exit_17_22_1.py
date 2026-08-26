import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
for rel in ("systems/guild_system.py","db_modules/systems_wrappers.py","db_modules/__init__.py","handlers/guild.py"): ast.parse((R/rel).read_text(encoding="utf-8"),filename=rel)
s=(R/"systems/guild_system.py").read_text(encoding="utf-8");t=ast.parse(s)
promote_nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="promote_guild_member_to_officer"]
assert len(promote_nodes)==1
assert "FINAL OVERRIDE" not in (ast.get_docstring(promote_nodes[0]) or "")
assert not any(isinstance(n,(ast.Assign,ast.AnnAssign)) and any(isinstance(x,ast.Name) and x.id=="_base_promote_guild_member_to_officer_before_single_officer_v1" for x in (n.targets if isinstance(n,ast.Assign) else [n.target])) for n in t.body)
import db
assert callable(db.transfer_guild_leadership) and callable(db.transfer_guild_leadership_and_leave)
h=(R/"handlers/guild.py").read_text(encoding="utf-8")
for token in ("👑 Передати керівництво","guild_leadership_select:","guild_leadership_confirm:","transfer_guild_leadership_and_leave"): assert token in h,token
print("[PASS] Stage 17.22.1 canonical leadership transfer contract")