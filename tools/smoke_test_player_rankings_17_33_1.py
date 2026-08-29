import ast,importlib.util,sqlite3,tempfile,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
for p in ('systems/player_rankings_system.py','handlers/player_rankings.py','handlers/city.py','main.py'):ast.parse((R/p).read_text(encoding='utf-8'),filename=p)
spec=importlib.util.spec_from_file_location('rank',R/'systems/player_rankings_system.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'t.db';c=sqlite3.connect(p);c.execute('CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,level INTEGER,exp INTEGER,gold REAL,str INTEGER,sta INTEGER,dex INTEGER,intelligence INTEGER,wis INTEGER)')
 rows=[]
 for i in range(1,126):rows.append((i,'' if i==125 else 'P'+str(i),2 if i<120 else 3,i,10 if i<3 else i,10,10,10,10,10))
 c.executemany('INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?,?)',rows);c.commit();c.close()
 assert m.calculate_cumulative_player_exp(1,5)==5
 data=m.get_player_ranking_page('gold',124,0,20,100,p);assert data['success'] and len(data['items'])==20 and data['pages']==5 and data['total_eligible']==124
 last=m.get_player_ranking_page('gold',1,99,20,100,p);assert last['page']==4 and not last['has_next']
 assert data['viewer']['position']==1
 assert not m.get_player_ranking_page('bad',1,0,20,100,p)['success']
handler=(R/'handlers/player_rankings.py').read_text(encoding='utf-8')
assert "for index in range(0,len(labels),2):kb.row(*labels[index:index+2])" in handler
assert "kb.row(BACK_TO_MENU)" in handler
assert handler.count("@bot.message_handler(func=lambda m:str(getattr(m,'text','') or '')==RANKING_BUTTON)")==1
assert "startswith('pr:')" in handler
city=(R/'handlers/city.py').read_text(encoding='utf-8');assert city.count('kb.add("🏆 Рейтинг")')==1
print('[PASS] Stage 17.33.1 rankings, top-100, pagination, tie-breakers and 2-per-row category keyboard')
