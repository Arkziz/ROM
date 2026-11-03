import ast
from pathlib import Path
T={"systems/character_system.py":("grant_class_change_available","consume_class_change_available","confirm_character_class_change_17_13_1","apply_lazy_mp_regeneration_17_15_1","apply_post_combat_mp_floor_17_15_1"),"systems/contract_system.py":("create_daily_contract","abandon_active_contract","process_contract_progress_on_kill","_claim_contract_reward_base"),"systems/energy_system.py":("consume_energy_for_hunt","get_users_for_energy_full_notification","get_user_energy")}
for p,names in T.items():
 t=ast.parse(Path(p).read_text(encoding="utf-8-sig")); d=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
 for n in names:
  m=[x for x in d if x.name==n]; assert len(m)==1,(p,n,len(m)); calls=[x for x in ast.walk(m[0]) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]; assert any(x.func.attr=="commit" for x in calls),(p,n,"commit"); assert any(x.func.attr=="rollback" for x in calls),(p,n,"rollback")
print("PASS: Stage 21.4.13 exact character, contract and energy owner rollback invariants")
