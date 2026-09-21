#!/usr/bin/env python3
import sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import handlers.city as city
with patch.object(city,'get_wallet',return_value=0.22):
 result=city.build_blacksmith_text(1)
assert isinstance(result,tuple),type(result)
assert len(result)==2,len(result)
text,kb=result
assert isinstance(text,str),type(text)
assert kb is not None
assert text.startswith('⚒️ Коваль'),repr(text)
assert 'Коваль ремонтує пошкоджене спорядження' in text,repr(text)
assert 'Каменів Посилення' in text,repr(text)
assert '🛠️ Ремонт спорядження' in text,repr(text)
assert '✨ Заточка спорядження' in text,repr(text)
assert '💰 Золото: 0.22' in text,repr(text)
print('[PASS] public blacksmith builder returns exactly text and keyboard')
