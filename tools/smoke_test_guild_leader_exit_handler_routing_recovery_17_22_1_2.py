import ast,importlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
p=R/"handlers/guild.py";s=p.read_text(encoding="utf-8");t=ast.parse(s)
regs=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="register_guild_handlers"];assert regs
r=regs[-1];names=("guild_leave_prompt_17_21_1","guild_leave_callback_17_21_1","guild_leadership_start_17_22_1","guild_leadership_callback_17_22_1")
found={n.name:n for n in r.body if isinstance(n,ast.FunctionDef) and n.name in names};assert set(found)==set(names),found
chains=[]
for statement in r.body:
    receives=False
    for call in (n for n in ast.walk(statement) if isinstance(n,ast.Call)):
        if any(isinstance(a,ast.Name) and a.id=="bot" for a in call.args) or any(k.arg=="bot" and isinstance(k.value,ast.Name) and k.value.id=="bot" for k in call.keywords): receives=True
    if receives: chains.append(statement)
assert chains
assert max(found[x].lineno for x in names)<min(n.lineno for n in chains)
module=importlib.import_module("handlers.guild")
for name in ("get_user_guild_role","transfer_guild_leadership","transfer_guild_leadership_and_leave"):assert callable(getattr(module,name,None)),name
leave_node=found["guild_leave_prompt_17_21_1"]
leave_source=ast.get_source_segment(s,leave_node) or ""
decorator_constants={n.value for decorator in leave_node.decorator_list for n in ast.walk(decorator) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
assert "🚪 Покинути гільдію" in decorator_constants
assert "_guild_leadership_candidates_17_22_1" in leave_source
assert "_guild_leadership_select_kb_17_22_1" in leave_source
leave_constants={n.value for n in ast.walk(leave_node) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
assert "leave" in leave_constants
callback_source=ast.get_source_segment(s,found["guild_leadership_callback_17_22_1"]) or ""
assert "transfer_guild_leadership_and_leave" in callback_source
print("[PASS] Stage 17.22.1.2 leader exit routes precede legacy guild handlers")
