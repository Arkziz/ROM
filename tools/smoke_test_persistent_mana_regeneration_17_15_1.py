#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));DB=ROOT/"game.db"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
before=sha(DB)
for rel in ("systems/character_system.py","handlers/combat.py","systems/notifications.py","systems/potion_system.py"):
 s=(ROOT/rel).read_text(encoding="utf-8");ast.parse(s);assert s.count("ROM 17.15.1 PERSISTENT MANA REGENERATION")==1,rel
char=(ROOT/"systems/character_system.py").read_text(encoding="utf-8")
for token in ("last_mp_regen_update","mp_full_notified","mp_regen_paused","def apply_lazy_mp_regeneration_17_15_1","def apply_post_combat_mp_floor_17_15_1","def begin_mp_combat_pause_17_15_1"):
 assert token in char
combat=(ROOT/"handlers/combat.py").read_text(encoding="utf-8")
assert "restore_user_mp_to_full(user_id)" not in combat
assert combat.count("apply_post_combat_mp_floor_17_15_1(user_id)")==5
assert "begin_mp_combat_pause_17_15_1(user_id)" in combat
notify=(ROOT/"systems/notifications.py").read_text(encoding="utf-8")
assert "notify_mp_restored_17_15_1(bot_instance, conn)" in notify
assert "Мана повністю відновлена" in notify
assert notify.index("bot_instance.send_message") < notify.rfind("mp_full_notified=1")
potion=(ROOT/"systems/potion_system.py").read_text(encoding="utf-8")
assert "_BASE_USE_POTION_FROM_INVENTORY_17_15_1" in potion
assert sha(DB)==before
print("[PASS] Stage 17.15.1 persistent mana regeneration contract")
