#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
before=sha(R/"game.db")
files=("data/equipment_profiles.py","systems/dynamic_equipment_system.py","db_modules/generated_equipment.py","db_modules/dev_compat.py","systems/equipment_system.py")
for rel in files:
 s=(R/rel).read_text(encoding="utf-8");ast.parse(s);assert s.count("ROM 17.17.1.5 WARRIOR SMALL SHIELD")==1,rel
sys.path.insert(0,str(R))
from data.equipment_profiles import OFF_HAND_PROFILES,OFF_HAND_ALLOWED_BY_CLASS,ITEM_SUBTYPE_LABELS
assert OFF_HAND_PROFILES["warrior_shield"]["name"]=="Малий щит"
assert OFF_HAND_ALLOWED_BY_CLASS["warrior"]==["warrior_shield"]
assert OFF_HAND_ALLOWED_BY_CLASS["knight"]==["shield"]
assert ITEM_SUBTYPE_LABELS["warrior_shield"]=="Малий щит"
for rel in files[1:4]:
 s=(R/rel).read_text(encoding="utf-8");assert 'profile_key == "warrior_shield"' in s;assert all(x in s for x in ('rarity, 0.81','rarity, 0.65','rarity, 0.35'))
s=(R/files[4]).read_text(encoding="utf-8");t=ast.parse(s);f=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=="equip_inventory_item"]
assert len(f)>=2
f=sorted(f,key=lambda n:n.lineno);src=ast.get_source_segment(s,f[-1]) or ""
assert "BEGIN IMMEDIATE" in src and "db.conn.rollback()" in src and "slot_key='off_hand'" in src
assert "_equipment_write_set_slot_v5" not in src
assert sha(R/"game.db")==before
print("[PASS] Stage 17.17.1.5 Warrior small shield contract")
