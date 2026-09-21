from __future__ import annotations
import contextlib,io,sys,tempfile
from pathlib import Path
from openpyxl import load_workbook
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
import tools.run_all_class_progression_matrix as matrix
results={}
for n,cls in enumerate(matrix.CLASSES):
 results[cls]={'target_reached':True,'final_level':5,'battles':50+n,'battle_outcomes':{'victory':45+n,'defeat':5,'escape':0},'encounters':{'normal':45+n,'elite':5,'boss':0},'economy':{'from_mobs':5+n,'from_item_sales':1.0,'repair_cost':.5,'final':5.5+n},'final_loadout':[],'loot_lifecycle':[{'item_id':100+n,'found':1,'equipped':0,'sold':0,'used_or_transformed':0,'remaining':1,'sale_gold':0}],'time_to_target':{'total_minutes':900+n},'exp_gained':700,'resources':{'hp_potions':{'found':3,'remaining':1},'refine_stones':{'found':1,'remaining':0},'runes':{'found':1,'remaining':0}},'canonical_result':{'events':[{'event_type':'simulation_final_state','details':{'refine_attempts':1,'refine_successes':1}}]}}
original=matrix.run_class_progression
try:
 matrix.run_class_progression=lambda root,request:results[request.character_class]
 output=io.StringIO()
 with contextlib.redirect_stdout(output):data=matrix.run_matrix(5,3,365)
 text=output.getvalue();assert data['target_level']==5 and len(data['results'])==6;assert '[PASS] warrior 1->5' in text and '[TIME RANKING]' in text
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'matrix5.xlsx';matrix.write_xlsx(data,p);wb=load_workbook(p);assert wb['Matrix Summary']['B2'].value==5;assert wb['Matrix Summary']['C2'].value=='0 d 15 h 0 min'
finally:matrix.run_class_progression=original
source=(R/'tools/run_all_class_progression_matrix.py').read_text(encoding='utf-8-sig');assert "target_level not in (2,5,10)" in source;assert 'supports target levels 2, 5, and 10 only' in source
print('[PASS] six-class target-level 5 matrix route, console time, and XLSX aggregate')
