from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.travel_system import is_user_travelling,get_active_travel
map_src=(ROOT/'handlers/map.py').read_text(encoding='utf-8-sig')
combat=(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig')
interaction=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
pvp=(ROOT/'handlers/pvp_interaction.py').read_text(encoding='utf-8-sig')
assert 'map:refresh:' in map_src and '🔄 Оновити' in map_src
assert 'if current!=CITY_NODE or current==CITY_NODE' not in map_src
assert 'callback_data="map:players"' in map_src
assert 'travel_id != int(active["id"])' in map_src
assert 'is_user_travelling(user_id)' in combat
assert interaction.count('is_user_travelling(')>=2
assert pvp.count('is_user_travelling(')>=2
assert 'busy_checker=lambda' in map_src
assert 'CITY_ACTION_BUTTONS' in map_src
assert 'def is_user_travelling' in (ROOT/'systems/travel_system.py').read_text(encoding='utf-8-sig')
print('[PASS] Stage 18.22.3 refresh, City players, stale ownership and PvE/PvP/trade/city travel guards')
