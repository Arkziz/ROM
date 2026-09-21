#!/usr/bin/env python3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import handlers.city as city
import handlers.runes as runes
with patch.object(city,'get_wallet',return_value=0.22):
 craft=city.build_craft_district_text(1)
 alch,_=city.build_alchemist_root_17_19_3(1)
 smith_result=city._BASE_BUILD_BLACKSMITH_TEXT_17_11_2(1)
 smith=smith_result[0] if isinstance(smith_result,tuple) else smith_result
with patch('db.get_rune_master_shop_state',return_value={'gold':0.22,'simple_price':10,'simple_owned':0,'perfect_owned':1}):
 shop,_=runes.build_rune_master_shop(1)
for text in (craft,alch,smith,shop):
 assert '💰 Золото:' in text,repr(text)
for stale in ('Придбання за кристали буде додано в майбутньому.','💰 Твоє золото:','💰 золото'):
 assert stale not in chr(10).join((craft,alch,smith,shop)),stale
assert '20 кристалів' in shop
assert '💠 Рунний Майстер' in craft
assert 'Каменів Посилення' in smith
assert 'купівля та продаж зіль' in craft
print('[PASS] city service texts use one normalized structure and current extractor availability')
