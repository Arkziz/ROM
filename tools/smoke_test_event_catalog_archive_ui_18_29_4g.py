# -*- coding: utf-8 -*-
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
s=(ROOT/"handlers"/"event_ui.py").read_text(encoding="utf-8");ast.parse(s)
c=(ROOT/"events"/"test_event_2026"/"config.py").read_text(encoding="utf-8-sig");ast.parse(c)
assert 'TITLE = "Тестовий івент"' in c
assert s.count("ROM_STAGE_18_29_4G_EVENT_CATALOG")==1
assert '🎉 Івенти\\n\\nОберіть івент:' in s
assert 'catalog:list:' in s and 'catalog:view:' in s
assert '🔙 До списку івентів' in s
assert 'completed=[row for row in _event_rows() if row["status"]=="completed"]' in s
assert 'Архів завершених івентів' in s
assert 'Завершених івентів поки немає.' in s
assert 'test_event_2026 — upcoming' not in s
assert 'status_order={"active":0,"upcoming":1,"completed":2}' in s
assert 'STATUS_LABELS={"active":"🟢 Активний","upcoming":"⏳ Незабаром","completed":"✅ Завершено"}' in s
print("EVENT_CATALOG_ARCHIVE_UI_18_29_4G_OK")
