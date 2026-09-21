#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
 sys.path.insert(0,str(ROOT))
from handlers.inventory import _get_rune_inventory_description
from data.runes import RUNE_EXTRACTOR_ITEM_ID, PERFECT_RUNE_EXTRACTOR_ITEM_ID
simple=_get_rune_inventory_description(RUNE_EXTRACTOR_ITEM_ID)
perfect=_get_rune_inventory_description(PERFECT_RUNE_EXTRACTOR_ITEM_ID)
literal_backslash_n=chr(92)+'n'
lf=chr(10)
for text in (simple,perfect):
 assert literal_backslash_n not in text, repr(text)
 assert lf+lf+'⚙️ Ефект:'+lf in text, repr(text)
 assert lf+lf+'🛒 Придбання:'+lf in text, repr(text)
assert 'Рунного Майстра за золото' in simple
assert 'Магазині кристалів за 20 кристалів' in perfect
print('[PASS] extractor descriptions render real Telegram line breaks')
