#!/usr/bin/env python3
from __future__ import annotations
import ast,json,sqlite3,subprocess,sys,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def assignment(text,name):
 tree=ast.parse(text);nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
 assert len(nodes)==1;return ast.literal_eval(nodes[0])
def run_tool(rel):
 q=subprocess.run([sys.executable,str(ROOT/rel)],cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=300)
 if q.returncode:raise AssertionError(q.stderr or q.stdout)
 assert '[OK]' in q.stdout
 return q.stdout.strip()
def main():
 files={x:(ROOT/x).read_text(encoding='utf-8-sig') for x in ('main.py','systems/timed_exp_bonus_system.py','handlers/timed_exp_bonus.py','systems/admin_crystal_credit_system.py','systems/crystal_shop_system.py','systems/crystal_bag_expansion_system.py')}
 for x,t in files.items():ast.parse(t,filename=x)
 assert assignment(files['systems/timed_exp_bonus_system.py'],'PLANS')=={15:100,30:180}
 assert "'15 днів — 100 💎'" in files['handlers/timed_exp_bonus.py'] and "'30 днів — 180 💎'" in files['handlers/timed_exp_bonus.py']
 assert 'BONUS_PERCENT=25' in files['systems/timed_exp_bonus_system.py'] and 'calculate_premium_combat_gold' in files['systems/timed_exp_bonus_system.py']
 assert assignment(files['systems/crystal_shop_system.py'],'CRYSTAL_SHOP_CATALOG')=={501:{'name':'🔮 Сфера нового шляху','price':150},602:{'name':'🍀 Руна Успіху','price':35},728:{'name':'💠 Досконалий Екстрактор','price':20},502:{'name':'✍️ Руна імені','price':50}}
 assert assignment(files['systems/crystal_bag_expansion_system.py'],'BAG_EXPANSION_TIERS')=={60:{'target_capacity':80,'price':75},80:{'target_capacity':100,'price':150}}
 main_t=files['main.py'];assert main_t.count('from systems.admin_crystal_credit_system import init_admin_crystal_credit_system')==1 and main_t.count('init_admin_crystal_credit_system()')==1
 assert main_t.index('init_admin_crystal_credit_system()')<main_t.index('register_admin_crystal_credit_handlers(bot)')
 assert 'CREATE TABLE IF NOT EXISTS admin_crystal_credit_audit' in files['systems/admin_crystal_credit_system.py']
 p54=run_tool('tools/smoke_test_stage_20_5_4_premium_prices.py');p56=run_tool('tools/smoke_test_stage_20_5_6_admin_crystal_schema.py')
 print('[OK] Stage 20.5.7 maintained Premium and admin crystal suites PASS')
 print(p54);print(p56)
if __name__=='__main__':main()
