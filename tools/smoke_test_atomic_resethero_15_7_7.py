from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
db_path = ROOT / "db.py"
handler_path = ROOT / "handlers" / "dev.py"
db_text = db_path.read_text(encoding="utf-8")
handler_text = handler_path.read_text(encoding="utf-8")
db_tree = ast.parse(db_text, filename=str(db_path))
handler_tree = ast.parse(handler_text, filename=str(handler_path))

functions = [node for node in db_tree.body if isinstance(node, ast.FunctionDef)]
reset_functions = [node for node in functions if node.name == "reset_hero_for_test"]
assert len(reset_functions) == 1, len(reset_functions)
segment = ast.get_source_segment(db_text, reset_functions[0]) or ""

required = (
    "BEGIN IMMEDIATE",
    "conn.rollback()",
    "conn.commit()",
    "PRAGMA foreign_keys=ON",
    "PRAGMA busy_timeout=30000",
    "PRAGMA foreign_key_check",
    "DELETE FROM inventory_runes",
    "DELETE FROM inventory_reservations",
    "DELETE FROM equipment_slots",
    "DELETE FROM inventory WHERE user_id=?",
    "UPDATE users SET",
    "ensure_equipment_slots(user_id)",
)
for token in required:
    assert token in segment, token

assert "DELETE FROM users" not in segment
assert segment.count("conn.rollback()") >= 2
assert "for attempt in range(1, 4)" in segment
assert "_get_dev_reset_hero_lock" in segment
assert 'if result.get("success") and user_id in bot.user_data' in handler_text
assert 'del bot.user_data[user_id]' in handler_text

print("[PASS] atomic resethero contract", {
    "delete_users": False,
    "rollback_paths": segment.count("conn.rollback()"),
    "lock_retries": 3,
    "handler_memory_cleanup": True,
})
