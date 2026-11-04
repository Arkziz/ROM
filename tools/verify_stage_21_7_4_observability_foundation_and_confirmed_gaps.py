import ast
from pathlib import Path
POINTS={'handlers/combat.py': [('safe_send_message', 3887, 'DELIVERY_FAILURE', 'combat.safe_send_message.primary'), ('safe_send_message', 3897, 'DELIVERY_FAILURE', 'combat.safe_send_message.fallback')], 'systems/notifications.py': [('notify_energy_full', 444, 'DELIVERY_FAILURE', 'notifications.energy_full'), ('notify_hp_restored', 464, 'DELIVERY_FAILURE', 'notifications.hp_restored'), ('notification_worker', 511, 'WORKER_FAILURE', 'notifications.worker.connect'), ('notify_mp_restored_17_15_1', 956, 'DELIVERY_FAILURE', 'notifications.mp_restored'), ('notification_worker', 516, 'WORKER_FAILURE', 'notifications.worker.fetch'), ('notification_worker', 522, 'WORKER_FAILURE', 'notifications.worker.dispatch')], 'systems/player_interaction_system.py': [('wrapped', 303, 'DOMAIN_FAILURE', 'player_interaction.decorator')], 'db_modules/migrations.py': [('run_db_startup_maintenance', 128, 'MIGRATION_FAILURE', 'migrations.startup.refine_stack'), ('run_db_startup_maintenance', 150, 'MIGRATION_FAILURE', 'migrations.startup.contract_targets')]}
def owner(tree,node):
 p={c:x for x in ast.walk(tree) for c in ast.iter_child_nodes(x)};cur=node
 while cur in p:
  cur=p[cur]
  if isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef)):return cur
 return None
pl=Path("systems/production_logging.py").read_text(encoding="utf-8-sig")
for token in ("OBSERVABILITY_ERROR_CATEGORIES","normalize_error_category","new_operation_id","_redact_observability_value","log_observability_exception"):assert token in pl,token
shop=ast.parse(Path("db_modules/shop.py").read_text(encoding="utf-8-sig")); fn=[n for n in ast.walk(shop) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="create_common_equipment_shop_preview"]; assert len(fn)==1; handlers=[n for n in ast.walk(fn[0]) if isinstance(n,ast.ExceptHandler)]; assert handlers and all(n.type is not None for n in handlers)
for path,rows in POINTS.items():
 text=Path(path).read_text(encoding="utf-8-sig");tree=ast.parse(text)
 for fn,line,category,phase in rows:
  marker=f'log_observability_exception("{category}", "{phase}")'
  assert text.count(marker)==1,(path,marker)
print("PASS: Stage 21.7.4 observability source contract")
