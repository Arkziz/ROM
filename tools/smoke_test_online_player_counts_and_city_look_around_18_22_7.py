from __future__ import annotations
import ast,sqlite3,sys,tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

system=(ROOT/'systems/player_interaction_system.py').read_text(encoding='utf-8-sig')
city=(ROOT/'handlers/city.py').read_text(encoding='utf-8-sig')
keyboards=(ROOT/'keyboards.py').read_text(encoding='utf-8-sig')
for name,src in (('system',system),('city',city),('keyboards',keyboards)):ast.parse(src,filename=name)

def function(src,name):
 tree=ast.parse(src);nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
 assert len(nodes)==1,(name,len(nodes));return nodes[0]
assert 'PLAYER_ONLINE_TIMEOUT_SECONDS = 300' in system
counts_node=function(system,'get_online_player_counts')
ns={}
for helper in ('_connect','_now','_text','_users_column_names','_pick_user_column'):
 node=function(system,helper);exec(compile(ast.Module([node],[]),'system','exec'),ns)
ns['PLAYER_ONLINE_TIMEOUT_SECONDS']=300;ns['datetime']=datetime;ns['timedelta']=timedelta;ns['timezone']=timezone;ns['Path']=Path;ns['sqlite3']=sqlite3
exec(compile(ast.Module([counts_node],[]),'system','exec'),ns)
with tempfile.TemporaryDirectory() as td:
 db=Path(td)/'test.db';con=sqlite3.connect(db)
 con.execute('CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT)')
 now=datetime(2026,9,13,12,0,tzinfo=timezone.utc)
 fresh=(now-timedelta(seconds=299)).isoformat(timespec='seconds');expired=(now-timedelta(seconds=301)).isoformat(timespec='seconds')
 con.executemany('INSERT INTO users VALUES(?,?,?,?)',[(1,'A','city',fresh),(2,'B','city',fresh),(3,'C','start_path',fresh),(4,'D','city',expired),(5,'','city',fresh)])
 con.commit();con.close()
 result=ns['get_online_player_counts'](1,now=now,db_path=db)
 assert result['success'] and result['online_total']==3 and result['online_here']==2,result
 assert result['includes_viewer'] is True and result['timeout_seconds']==300
 result2=ns['get_online_player_counts'](3,now=now,db_path=db)
 assert result2['online_total']==3 and result2['online_here']==1,result2

city_kb_node=function(keyboards,'city_kb');kb_src=ast.get_source_segment(keyboards,city_kb_node) or ''
assert 'kb.add("👀 Роззирнутися", "🗺️ Мапа")' in kb_src
assert city.count('_online_presence_block_18_22_7(user_id, city=True)')==1
assert city.count('_online_presence_block_18_22_7(user_id, city=False)')==1
assert 'get_online_players_in_same_location' in system and 'user_id<>?' in system
print('{"status":"PASS","timeout_seconds":300,"total_includes_viewer":true,"location_includes_viewer":true,"selectable_list_excludes_viewer":true,"city_row":"look_around_plus_map"}')
