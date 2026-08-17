from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
path=ROOT/"db_modules"/"systems_wrappers.py"
text=path.read_text(encoding="utf-8"); ast.parse(text,filename=str(path))
assert '_guild_system().get_user_guild_profile_line' not in text
from db import get_user_guild_profile_line
assert callable(get_user_guild_profile_line)
class FakeGuildSystem:
    def __init__(self,guild=None): self.guild=guild
    def get_user_guild(self,user_id): return self.guild
    def get_guild_display_name(self,guild): return "🏰 [ROM] Test Guild"
    def get_user_guild_role(self,user_id): return "member"
    def get_guild_role_label(self,role): return "👤 Учасник"
import db_modules.systems_wrappers as wrappers
original=wrappers._guild_system
try:
    wrappers._guild_system=lambda: FakeGuildSystem(None)
    assert wrappers.get_user_guild_profile_line(1)=="🏰 Гільдія: Без гільдії"
    wrappers._guild_system=lambda: FakeGuildSystem({"id":1})
    value=wrappers.get_user_guild_profile_line(1)
    assert "[ROM] Test Guild" in value and "👤 Учасник" in value
finally:
    wrappers._guild_system=original
print("[PASS] guild profile line runtime contract")
