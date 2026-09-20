from __future__ import annotations
import contextlib,io,sys,tempfile
from pathlib import Path
from openpyxl import load_workbook
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
import tools.run_all_class_progression_matrix as matrix
assert matrix.format_duration(313)=='0 d 5 h 13 min'
results={}
for n,cls in enumerate(matrix.CLASSES):
 results[cls]={'target_reached':True,'final_level':10,'battles':100+n,'battle_outcomes':{'victory':90+n,'defeat':10,'escape':0},'encounters':{'normal':90+n,'elite':10,'boss':0},'economy':{'from_mobs':10+n,'from_item_sales':1.0,'repair_cost':.5,'final':10.5+n},'final_loadout':[],'loot_lifecycle':[{'item_id':100+n,'found':1,'equipped':0,'sold':0,'used_or_transformed':0,'remaining':1,'sale_gold':0}],'time_to_target':{'total_minutes':1500+n},'exp_gained':1000,'resources':{'hp_potions':{'found':3,'remaining':1},'refine_stones':{'found':1,'remaining':0},'runes':{'found':1,'remaining':0}},'canonical_result':{'events':[{'event_type':'simulation_final_state','details':{'refine_attempts':1,'refine_successes':1}}]}}
original=matrix.run_class_progression
try:
 matrix.run_class_progression=lambda root,request:results[request.character_class]
 output=io.StringIO()
 with contextlib.redirect_stdout(output):data=matrix.run_matrix(10,3,365)
 text=output.getvalue();assert data['target_level']==10 and len(data['results'])==6;assert '[TIME RANKING]' in text;assert '[PASS] warrior 1->10' in text
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'matrix10.xlsx';matrix.write_xlsx(data,p);wb=load_workbook(p);assert wb['Matrix Summary']['B2'].value==10;assert wb['Matrix Summary']['C2'].value=='1 d 1 h 0 min'
finally:matrix.run_class_progression=original
source=(R/'tools/run_all_class_progression_matrix.py').read_text(encoding='utf-8-sig');assert "target_level not in (2,10)" in source;assert 'fixed to target level 2' not in source
print('[PASS] six-class target-level 10 matrix route, console time, and XLSX aggregate')
