import ast, importlib, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
system=(R/"systems/guild_system.py").read_text(encoding="utf-8")
handler=(R/"handlers/guild.py").read_text(encoding="utf-8")
st=ast.parse(system); ht=ast.parse(handler)
assert "MIN_GUILD_ACCESS_LEVEL = 3" in system
for name in ("create_guild","create_guild_application","accept_guild_application","get_guild_creation_terms"):
    nodes=[n for n in st.body if isinstance(n,ast.FunctionDef) and n.name==name]
    assert nodes, name
    assert "get_guild_access_level_state" in (ast.get_source_segment(system,nodes[-1]) or ""), name
halls=[n for n in ht.body if isinstance(n,ast.FunctionDef) and n.name=="guild_hall_kb"]
active=ast.get_source_segment(handler,halls[-1]) or ""
assert 'kb.row("🚪 Покинути гільдію", "👑 Передати керівництво")' in active
assert active.find("👑 Передати керівництво") < active.find("🔙 Місто")
starts=[n for n in ht.body if isinstance(n,ast.FunctionDef) and n.name=="start_guild_creation"]
assert "level_allowed" in (ast.get_source_segment(handler,starts[-1]) or "")
constant_nodes=[n for n in st.body if isinstance(n,(ast.Assign,ast.AnnAssign))]
assert any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="MIN_GUILD_ACCESS_LEVEL" for t in n.targets) and isinstance(n.value,ast.Constant) and n.value.value==3 for n in constant_nodes)
print("[PASS] Stage 17.23.1.1.1 static level gate and button layout contract")
