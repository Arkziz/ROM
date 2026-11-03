import ast
from pathlib import Path
T={"systems/notifications.py":("apply_energy_regen","get_users_for_energy_full_notification_worker","get_users_for_hp_full_notification_worker","get_worker_max_hp","apply_hp_regen","apply_mp_regen_worker_17_15_1","notify_mp_restored_17_15_1"),"systems/regen_system.py":("_sync_max_hp","apply_passive_hp_regen","process_passive_regeneration")}
for p,names in T.items():
 t=ast.parse(Path(p).read_text(encoding="utf-8-sig")); ds=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
 for n in names:
  m=[x for x in ds if x.name==n]; assert m,(p,n,"missing"); fn=m[-1]; calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]; assert any(x.func.attr=="commit" for x in calls),(p,n,"commit"); assert any(x.func.attr=="rollback" for x in calls),(p,n,"rollback"); assert any(isinstance(h,ast.ExceptHandler) and any(isinstance(r,ast.Raise) for r in ast.walk(h)) for h in ast.walk(fn)),(p,n,"reraise")
print("PASS: Stage 21.4.15 active regeneration-worker rollback invariants")
