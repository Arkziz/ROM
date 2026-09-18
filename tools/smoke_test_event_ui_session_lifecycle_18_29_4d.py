# -*- coding: utf-8 -*-
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
s=(ROOT/"handlers"/"event_ui.py").read_text(encoding="utf-8");ast.parse(s)
assert "_ACTIVE_EVENT_UI={}" in s
assert "ReplyKeyboardMarkup" in s and "kb.add(BACK_BUTTON)" in s
assert "delete_message" in s and "edit_message_reply_markup" in s
assert 'm.text==BACK_BUTTON and int(m.from_user.id) in _ACTIVE_EVENT_UI' in s
assert 'if not _valid(call)' in s and "Це меню вже неактивне." in s
assert '_ACTIVE_EVENT_UI[uid]={' in s and 'message_id' in s
city=(ROOT/"handlers"/"city.py").read_text(encoding="utf-8-sig");ast.parse(city)
assert "kb.row('📜 Хроніки світу', '🎉 Івенти')" in city
assert "kb.add('📜 Хроніки світу')" not in city
print("EVENT_UI_SESSION_LIFECYCLE_18_29_4D_OK")
