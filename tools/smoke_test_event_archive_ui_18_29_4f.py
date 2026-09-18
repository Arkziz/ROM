# -*- coding: utf-8 -*-
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
s=(ROOT/"handlers"/"event_ui.py").read_text(encoding="utf-8");ast.parse(s)
assert s.count("ROM_STAGE_18_29_4F_EVENT_ARCHIVE")==1
assert 'InlineKeyboardButton("📚 Архів"' in s
assert 'ARCHIVE_PAGE_SIZE=5' in s
assert 'status_order={"active":0,"upcoming":1,"completed":2}' in s
assert 'completed_read_only' in s
assert 'archive:list:' in s and 'archive:view:' in s
assert 'Цей івент ще не завершено.' in s
assert 'Історичний рейтинг' in s
assert 'card_message_id' in s and '_edit(bot,call' in s
print("EVENT_ARCHIVE_UI_18_29_4F_OK")
