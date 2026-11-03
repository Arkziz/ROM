import ast
from pathlib import Path
T={"db_modules/daily_compat.py":("reset_daily_quest_if_needed",),"db_modules/location.py":("set_current_location",),"systems/character_system.py":("set_character_name","refresh_user_mp","set_user_mp","set_character_class","reset_mp_regen_clock_17_15_1"),"systems/contract_system.py":("reset_daily_contracts_if_needed","reset_daily_hunts_if_needed"),"systems/energy_system.py":("reset_daily_hunts_if_needed",),"systems/guild_system.py":("_guild_safe_set_application_status",),"systems/player_system.py":("set_current_hp",)}
for p,names in T.items():
 t=ast.parse(Path(p).read_text(encoding="utf-8-sig")); ds=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
 for n in names:
  m=[x for x in ds if x.name==n]; assert m,(p,n,"missing"); fn=m[-1]; calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]; assert any(x.func.attr=="commit" for x in calls),(p,n,"commit"); assert any(x.func.attr=="rollback" for x in calls),(p,n,"rollback"); assert any(isinstance(h,ast.ExceptHandler) and any(isinstance(r,ast.Raise) for r in ast.walk(h)) for h in ast.walk(fn)),(p,n,"reraise")
print("PASS: Stage 21.4.18 final focused owner rollback invariants")
