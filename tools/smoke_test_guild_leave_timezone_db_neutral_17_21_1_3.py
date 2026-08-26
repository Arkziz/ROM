#!/usr/bin/env python3
import ast
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / "systems/guild_system.py").read_text(encoding="utf-8")
tree = ast.parse(source, filename="systems/guild_system.py")
assert "datetime.now(_guild_timezone_17_21_1.utc)" in source
assert "value.astimezone(_guild_timezone_17_21_1.utc).isoformat()" in source
assert "datetime.now(_guild_timezone_17_21_1)" not in source
assert "value.astimezone(_guild_timezone_17_21_1).isoformat()" not in source
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
namespace = {"datetime": datetime, "_guild_timezone_17_21_1": timezone}
for name in ("_guild_utc_now_17_21_1", "_guild_utc_iso_17_21_1", "_guild_parse_utc_17_21_1"):
    assert name in functions, name
    module = ast.Module(body=[functions[name]], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, "<guild-time-helper>", "exec"), namespace)
now = namespace["_guild_utc_now_17_21_1"]()
assert now.tzinfo is not None and now.utcoffset().total_seconds() == 0
text = namespace["_guild_utc_iso_17_21_1"](now)
assert text.endswith("+00:00"), text
parsed = namespace["_guild_parse_utc_17_21_1"](text)
assert parsed is not None and parsed.utcoffset().total_seconds() == 0
print("[PASS] Stage 17.21.1.3 DB-neutral UTC timezone smoke")
