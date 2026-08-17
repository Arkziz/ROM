from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db_modules.systems_wrappers as wrappers
class FakeGuildSystem:
    def __init__(self,guild): self.guild=guild
    def get_user_guild(self,user_id): return self.guild
original=wrappers._guild_system
try:
    wrappers._guild_system=lambda: FakeGuildSystem(None)
    assert wrappers.get_user_guild_profile_line(1)=="🏰 Гільдія: Без гільдії\n"
    wrappers._guild_system=lambda: FakeGuildSystem({"icon":"🍒","tag":"ВВП","name":"Вишня вам не помідор"})
    value=wrappers.get_user_guild_profile_line(1)
    assert value=="🏰 Гільдія: 🍒 [ВВП]\n",repr(value)
    assert "Роль" not in value
    assert "Вишня вам не помідор" not in value
finally:
    wrappers._guild_system=original
print("[PASS] compact guild profile line restored")
