#!/usr/bin/env python3
from pathlib import Path
import ast,sys,types
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
# Import real module, then call canonical terminal formatter with isolated contexts.
import handlers.combat as combat
skill={"name":"🏹 Прицільний постріл","no_damage":False}
mob={"name":"🦇 Лісовий кажан","hp":7,"max_hp":90}
base={"skill":skill,"mob":mob,"dmg":0,"enemy_action_text":"👹 Ворог атакував."}
miss=combat.build_lethal_combat_log(dict(base,skill_hit=False),1,160,[])
assert "💨 ПРОМАХ! Навичка «🏹 Прицільний постріл» не влучила в ціль." in miss
assert "Ти завдав 0 шкоди" not in miss
hit=combat.build_lethal_combat_log(dict(base,skill_hit=True,dmg=10),1,160,[])
assert "Ти завдав 10 шкоди" in hit
support=combat.build_lethal_combat_log({"skill":{"name":"🧱 Святий захист","no_damage":True},"skill_hit":True,"mob":mob},1,160,[])
assert "Навичка застосована" in support
source=(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")
assert source.count("💨 ПРОМАХ! Навичка «{}» не влучила в ціль.")==3
print("PVE_SKILL_MISS_TERMINAL_LOG_18_21_6A_OK")
