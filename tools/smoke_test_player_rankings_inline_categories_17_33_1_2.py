import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
p=R/'handlers/player_rankings.py';s=p.read_text(encoding='utf-8');ast.parse(s)
assert 'def player_rankings_exit_kb():' in s
assert 'kb.row(BACK_TO_MENU)' in s
assert 'def player_rankings_category_inline_kb():' in s
assert "callback_data=f'pr:category:{key}'" in s
assert 'for index in range(0,len(buttons),2):kb.row(*buttons[index:index+2])' in s
assert "if data.startswith('pr:category:'):" in s
assert "reply_markup=player_rankings_category_inline_kb()" in s
assert "callback_data='pr:categories'" in s
assert 'def player_rankings_category_kb():' not in s
assert "str(getattr(m,'text','') or '') in LABEL_TO_KEY" not in s
assert 'нижній клавіатурі' not in s
assert s.count("@bot.message_handler(func=lambda m:str(getattr(m,'text','') or '')==BACK_TO_MENU)")==1
assert s.count("@bot.callback_query_handler(func=lambda c:str(getattr(c,'data','') or '').startswith('pr:'))")==1
print('[PASS] Stage 17.33.1.2 inline categories, two per row, and persistent Back-to-Menu only')
