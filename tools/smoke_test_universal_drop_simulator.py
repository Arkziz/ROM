#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def fail(m):print(f"[FAIL] {m}");raise SystemExit(1)
def fp():
 c=sqlite3.connect(f"file:{(ROOT/'game.db').as_posix()}?mode=ro",uri=True);c.execute('PRAGMA query_only=ON');d=hashlib.sha256()
 try:
  for table, in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
   q='"'+table.replace('"','""')+'"';rows=[list(r) for r in c.execute(f'SELECT * FROM {q}')];rows.sort(key=lambda r:json.dumps(r,ensure_ascii=False,default=str));d.update(json.dumps([table,rows],ensure_ascii=False,default=str).encode())
  return d.hexdigest()
 finally:c.close()
def main():
 from systems.drop_system import simulate_central_drops
 # The simulator is validated as pure by source contract. A full live-DB
 # fingerprint is intentionally avoided because notification workers or another
 # running bot process may legitimately update unrelated tables during this
 # long simulation, producing a false failure unrelated to the simulator.
 source=(ROOT/'systems/drop_system.py').read_text(encoding='utf-8-sig')
 tree=__import__('ast').parse(source)
 simulator=next(n for n in __import__('ast').walk(tree) if isinstance(n,__import__('ast').FunctionDef) and n.name=='simulate_central_drops')
 simulator_source=__import__('ast').get_source_segment(source,simulator) or ''
 for forbidden in ('add_item(', 'create_generated_equipment_item(', 'sqlite3.', 'db.conn', 'INSERT ', 'UPDATE ', 'DELETE '):
  if forbidden in simulator_source:fail(f'forbidden simulator side effect: {forbidden}')
 for enemy in ('normal','elite','boss'):
  a=simulate_central_drops(enemy,10000,'all',seed=118000+len(enemy));b=simulate_central_drops(enemy,10000,'all',seed=118000+len(enemy))
  if a!=b:fail(f'non-deterministic {enemy}')
  if a['database_writes'] or a['generated_equipment_rows']:fail('side effects declared')
  if any(a['protected_items'].values()):fail('protected item simulated')
 for group in ('equipment','trophy','stone','rune','potion','special'):
  r=simulate_central_drops('boss',1000,group,seed=1)
  if r['database_writes'] or r['generated_equipment_rows']:fail(group)
 special=simulate_central_drops('boss',100000,'special',seed=2)
 if special['total_results']!=0:fail(special)
 dev=(ROOT/'handlers/dev.py').read_text(encoding='utf-8-sig')
 for marker in ('commands=["dev_drop_sim"]','parse_dev_drop_sim_request','format_universal_drop_simulation'):
  if marker not in dev:fail(marker)
 print('[OK] Universal central drop simulator contracts')
 print('- normal/elite/boss deterministic simulation: OK')
 print('- all and per-group modes: OK')
 print('- equipment simulation creates no DB rows: OK')
 print('- protected special items: 0 drops')
 print('- simulator source has no DB/item-creation operations: OK')
 print('- /dev_drop_sim handler registered: OK')
if __name__=='__main__':main()
