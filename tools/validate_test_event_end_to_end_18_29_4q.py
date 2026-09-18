# -*- coding: utf-8 -*-
import ast
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from events.test_event_2026 import config
from events.test_event_2026.items import get_item_definitions

assert config.ENABLED is True
assert config.TIMEZONE_NAME == "Europe/Kyiv"
assert config.DATE_POLICY == "EUROPE_KYIV_LOCAL_CANONICAL"
assert config.START_AT < config.END_AT
assert config.is_active(config.START_AT)
assert not config.is_active(config.END_AT)
assert not config.is_active(datetime.now(timezone.utc)), "event must be completed at finalization"

items = {int(item["id"]): item for item in get_item_definitions()}
assert items[4000]["category"] == "material"
assert items[4001]["category"] == "material"
assert items[4000]["tradeable"] is False
assert items[4001]["tradeable"] is False

conn = sqlite3.connect(f"file:{(ROOT / 'game.db').as_posix()}?mode=ro", uri=True)
try:
    assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    assert not conn.execute("PRAGMA foreign_key_check").fetchall()
    catalog = conn.execute(
        "SELECT id,name,category,max_stack FROM items WHERE id IN (4000,4001) ORDER BY id"
    ).fetchall()
    assert catalog == [
        (4000, "🧪 Експериментальний жетон", "material", 999),
        (4001, "🎁 Пам’ятний знак випробування", "material", 10),
    ], catalog
    assert conn.execute(
        "SELECT COUNT(*) FROM event_kill_statistics WHERE event_key=? AND mob_key=?",
        ("test_event_2026", "test_slime"),
    ).fetchone()[0] >= 1
    assert conn.execute(
        "SELECT COUNT(*) FROM event_shop_transactions WHERE event_key=?",
        ("test_event_2026",),
    ).fetchone()[0] >= 1
finally:
    conn.close()

combat = (ROOT / "systems" / "combat_system.py").read_text(encoding="utf-8")
handler = (ROOT / "handlers" / "combat.py").read_text(encoding="utf-8")
ui = (ROOT / "handlers" / "event_ui.py").read_text(encoding="utf-8")
for marker in (
    "# Stage 18.29.4l: canonical event-template materialization",
    "runtime_template = dict(base_template)",
):
    assert marker in combat
for marker in (
    "# Stage 18.29.4n: production-shaped event drop result contract",
    'reward.get("event_drop_results")',
    "🎉 Івентна нагорода:",
):
    assert marker in handler
for marker in (
    "# Stage 18.29.4o: Ukrainian victory forms and canonical guild tag",
    "g.tag",
    "Усього перемог:",
    'row["status"]=="completed"',
):
    assert marker in ui
assert "g.name FROM users" not in ui
assert '"category": "collectible"' not in (ROOT / "events" / "test_event_2026" / "items.py").read_text(encoding="utf-8")

print("TEST_EVENT_END_TO_END_18_29_4Q_OK")
