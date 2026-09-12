from __future__ import annotations
import ast
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

context = (ROOT / "systems/location_context_system.py").read_text(encoding="utf-8-sig")
interaction = (ROOT / "handlers/player_interaction.py").read_text(encoding="utf-8-sig")
combat = (ROOT / "handlers/combat.py").read_text(encoding="utf-8-sig")
city = (ROOT / "handlers/city.py").read_text(encoding="utf-8-sig")
for name, source in (("context", context), ("interaction", interaction), ("combat", combat), ("city", city)):
    ast.parse(source, filename=name)

assert "def get_location_context_kb" in context
assert "if kind == \"city\":" in context and "return city_kb()" in context
assert "if kind == \"travel\":" in context and "return map_kb()" in context
assert interaction.count("get_location_context_kb(") >= 4
assert interaction.count("get_location_context_return_text(") == 1
assert "Повернення до основного меню." not in interaction
assert "current_location == \"city\"" in combat
assert "У Місті не можна полювати" in combat
assert combat.index("current_location == \"city\"") < combat.index("consume_energy_for_hunt(user_id)")
assert "get_location_context_kind(user_id) == \"city\"" in city
assert "build_city_text(user_id)" in city and "reply_markup=city_kb()" in city
print("[PASS] Stage 18.22.3b city/travel/location context is restored after trade and City cannot hunt")
