from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.location_graph import LOCATION_GRAPH,TRAVEL_SECONDS
from handlers.map import build_map_inline_kb,MAP_COLLAPSE_BUTTON
from keyboards import map_kb
assert TRAVEL_SECONDS==60
assert LOCATION_GRAPH=={'city':('start_path',),'start_path':('city','dark_forest'),'dark_forest':('start_path',)}
assert MAP_COLLAPSE_BUTTON=='🔽 Згорнути мапу'
buttons=[(b.get('text') if isinstance(b,dict) else b.text) for row in map_kb().keyboard for b in row]
assert buttons==['🔽 Згорнути мапу']
src=(ROOT/'handlers/map.py').read_text(encoding='utf-8-sig')
assert 'set_current_location' not in src
for token in ('map:preview:','map:start:','map:cancel:','map:players','Повернутися у Місто'):
 assert token in src,token
assert "elif target=='start_path':" in src
assert "else: label=f" in src
assert "node['name'].split(' ',1)[-1]" in src
pi=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
assert 'render_map_message' in pi
travel=(ROOT/'systems/travel_system.py').read_text(encoding='utf-8-sig')
assert 'def start_travel_worker' in travel and 'def recover_travels_after_restart' in travel
main=(ROOT/'main.py').read_text(encoding='utf-8-sig')
assert 'start_travel_worker(bot)' in main and 'recover_travels_after_restart(bot)' in main
print('[PASS] Stage 18.22.2 inline map, travel UI, collapse keyboard, player return and arrival worker')
