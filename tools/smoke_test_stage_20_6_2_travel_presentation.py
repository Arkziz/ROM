#!/usr/bin/env python3
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main():
 files={x:(ROOT/x).read_text(encoding='utf-8-sig') for x in ('data/travel_presentation.py','handlers/map.py','systems/travel_system.py','data/location_graph.py')}
 for x,t in files.items():ast.parse(t,filename=x)
 from data.location_graph import WORLD_NODES,LOCATION_GRAPH,TRAVEL_SECONDS
 from data.travel_presentation import ROUTE_PRESENTATION,get_node_name,get_route_presentation,format_arrival_destination,CITY_MAP_INTRO,CITY_DESTINATION_SUMMARY
 assert TRAVEL_SECONDS==20 and set(WORLD_NODES)=={'city','start_path','dark_forest'}
 routes={(a,b) for a,bs in LOCATION_GRAPH.items() for b in bs};assert routes==set(ROUTE_PRESENTATION) and len(routes)==4
 assert all(set(v)=={'preview','active','arrival'} and all(v.values()) for v in ROUTE_PRESENTATION.values())
 assert get_node_name('start_path',WORLD_NODES)=='🌿 Початок Шляху'
 assert get_node_name('technical_unknown',WORLD_NODES)=='🧭 Невідома місцевість' and 'technical_unknown' not in get_node_name('technical_unknown',WORLD_NODES)
 assert format_arrival_destination('city',WORLD_NODES)=='Ти прибув до Міста.'
 assert format_arrival_destination('start_path',WORLD_NODES)=='Ти прибув до локації «Початок Шляху».'
 assert format_arrival_destination('dark_forest',WORLD_NODES)=='Ти прибув до Темного Бору.'
 assert CITY_MAP_INTRO and CITY_DESTINATION_SUMMARY
 map_t=files['handlers/map.py'];travel_t=files['systems/travel_system.py']
 assert 'Підтвердити подорож?' not in map_t
 assert '🚶 Вирушити' in map_t and '◀️ Повернутися до мапи' in map_t
 assert 'get_route_presentation' in map_t and 'get_route_presentation' in travel_t
 assert 'format_arrival_destination' in travel_t
 assert 'str(node_id)' not in ast.get_source_segment(map_t,next(n for n in ast.parse(map_t).body if isinstance(n,ast.FunctionDef) and n.name=='_node_name'))
 print('[OK] 4 routes, approved preview/active/arrival texts, city map info and safe fallback PASS')
if __name__=='__main__':main()
