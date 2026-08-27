import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'handlers/crystal_shop.py';s=p.read_text(encoding='utf-8');ast.parse(s)
for token in ('_close_shop_session','_active_shop_callback','_reject_stale_shop_callback','message_id','Це меню покупки вже неактивне.'):
 assert token in s,token
assert "def back(message):\n  _close_shop_session" in s
assert "stages=('confirm',)" in s
assert "stages=('quantity','confirm')" in s
print('[PASS] Stage 17.27.1.1 stale menu cleanup contract')
