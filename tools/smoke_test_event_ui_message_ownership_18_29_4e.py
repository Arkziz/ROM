# -*- coding: utf-8 -*-
import ast,sys,types as pytypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
source=(ROOT/"handlers"/"event_ui.py").read_text(encoding="utf-8");ast.parse(source)
assert 'EXIT_BUTTON="🔙 Вийти з івентів"' in source
assert 'm.text==EXIT_BUTTON' in source and 'm.text=="🔙 Назад"' not in source
assert '"scope_message_id"' in source and '"card_message_id"' in source
assert 'state["card_message_id"]=int(sent.message_id)' in source
assert source.index('state["card_message_id"]=int(sent.message_id)') < source.index('_delete(bot,state.get("chat_id"),old_id)')
assert '_delete(bot,state.get("chat_id") or chat_id,state.get("card_message_id"))' in source
assert '_delete(bot,state.get("chat_id") or chat_id,state.get("scope_message_id"))' in source
assert 'if not _valid(call)' in source and "Це меню вже неактивне." in source
assert '_delete(bot,old.get("chat_id"),old.get("card_message_id"))' in source
assert '_delete(bot,old.get("chat_id"),old.get("scope_message_id"))' in source
print("EVENT_UI_MESSAGE_OWNERSHIP_18_29_4E_OK")
