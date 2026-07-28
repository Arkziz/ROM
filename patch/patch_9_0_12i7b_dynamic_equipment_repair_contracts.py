#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i7b: install deterministic Dynamic Equipment and Repair Read contracts."""
from __future__ import annotations
import py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i7b"
TOOL_NAME="smoke_test_dynamic_equipment_repair_contracts.py"
TOOL=r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic, isolated contracts for remaining Dynamic Equipment duplicates."""
from __future__ import annotations
import copy
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db
from systems import equipment_system as equipment

TEST_USER_ID=-90120701
ARMOR_TYPES={"cloth","leather","chain","plate"}
STAT_KEYS={"bonus_str","bonus_dex","bonus_int","bonus_wis","bonus_sta","pdef","mdef"}


def fail(message):
 print(f"[FAIL] {message}"); raise SystemExit(1)

def user_tables():
 result=[]
 for (name,) in db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
  try: columns=[row[1] for row in db.conn.execute(f'PRAGMA table_info("{name}")').fetchall()]
  except Exception: continue
  if "user_id" in columns: result.append(name)
 return result

def cleanup_fixture():
 item_ids=[]
 try:
  item_ids=[int(r[0]) for r in db.conn.execute("SELECT item_id FROM inventory WHERE user_id=?",(TEST_USER_ID,)).fetchall()]
 except Exception: pass
 # Delete known dependent/user-owned rows first, then all remaining user_id tables.
 priority=["equipment_slots","auction_lots","inventory","user_active_contracts","user_daily_quests"]
 tables=user_tables()
 for table in priority+[x for x in tables if x not in priority and x!="users"]:
  try: db.conn.execute(f'DELETE FROM "{table}" WHERE user_id=?',(TEST_USER_ID,))
  except Exception: pass
 try: db.conn.execute("DELETE FROM users WHERE user_id=?",(TEST_USER_ID,))
 except Exception: pass
 for item_id in item_ids:
  try:
   refs=db.conn.execute("SELECT COUNT(*) FROM inventory WHERE item_id=?",(item_id,)).fetchone()[0]
   if int(refs or 0)==0: db.conn.execute("DELETE FROM items WHERE id=? AND COALESCE(is_generated,0)=1",(item_id,))
  except Exception: pass
 db.conn.commit()

def item_contract(result):
 if not isinstance(result,dict) or result.get("success") is not True: fail(f"generated item result failed: {result!r}")
 inventory_id=result.get("inventory_id")
 if not inventory_id: fail("generated item has no inventory_id")
 row=db.conn.execute(
  "SELECT inv.item_id,it.slot_key,it.rarity,it.item_level,it.is_generated,it.armor_type,it.item_subtype,"
  "it.bonus_str,it.bonus_dex,it.bonus_int,it.bonus_wis,it.bonus_sta,it.pdef,it.mdef "
  "FROM inventory inv JOIN items it ON it.id=inv.item_id WHERE inv.id=? AND inv.user_id=?",
  (int(inventory_id),TEST_USER_ID),
 ).fetchone()
 if not row: fail("generated inventory/item row missing")
 item_id,slot,rarity,level,is_generated,armor_type,subtype,*stats=row
 if int(is_generated or 0)!=1: fail("is_generated contract failed")
 if int(level or 0)<1: fail("item_level contract failed")
 if rarity not in {"common","uncommon","rare","epic"}: fail("rarity contract failed")
 if slot in {"helmet","shoulders","chest","gloves","legs","boots"} and armor_type not in ARMOR_TYPES: fail("armor_type contract failed")
 if slot in {"main_hand","off_hand"} and not str(subtype or ""): fail("weapon profile contract failed")
 if any(int(value or 0)<0 for value in stats): fail("negative generated stat")
 return int(item_id),int(inventory_id),str(slot)

def main():
 real_before=[tuple(r) for r in db.conn.execute("SELECT user_id FROM users WHERE user_id>=0 ORDER BY user_id").fetchall()]
 random_state=random.getstate()
 cleanup_fixture()
 checks=0
 try:
  # Idempotent schema initialization.
  if db.init_dynamic_equipment_system() is not None: pass
  db.init_dynamic_equipment_system(); checks+=1

  # Repair-read public/system equivalence for all current users.
  users=[int(r[0]) for r in db.conn.execute("SELECT user_id FROM users WHERE user_id>=0 ORDER BY user_id").fetchall()]
  repair_comparisons=0
  for uid in users:
   if db.get_equipped_items_for_repair(uid)!=equipment.get_equipped_items_for_repair(uid): fail(f"repair-read mismatch user={uid}")
   repair_comparisons+=1

  # Deterministic helper contracts.
  if db.detect_weapon_profile_from_name(None)!="": fail("empty weapon detection failed")
  helper_stats={"bonus_str":1,"bonus_dex":2,"bonus_int":3,"bonus_wis":4,"bonus_sta":5,"pdef":6,"mdef":7}
  budget=db.get_existing_primary_stat_budget(helper_stats)
  if budget!=15: fail(f"primary-stat budget mismatch: {budget}")
  cleared=copy.deepcopy(helper_stats); returned=db.clear_primary_stat_bonuses(cleared)
  if any(cleared[k]!=0 for k in ("bonus_str","bonus_dex","bonus_int","bonus_wis","bonus_sta")): fail("clear primary stats failed")
  db.add_primary_stat_to_stats(cleared,"str",3)
  if cleared.get("bonus_str")!=3: fail("add primary stat failed")
  checks+=4

  weighted=(("str",10),("dex",5),("wis",1))
  random.seed(20701); first=[db.pick_weighted_stat(weighted) for _ in range(12)]
  random.seed(20701); second=[db.pick_weighted_stat(weighted) for _ in range(12)]
  if first!=second or not set(first)<={"str","dex","wis"}: fail("weighted-stat deterministic contract failed")
  random.seed(20702); armor_first=[db.get_random_loot_armor_type() for _ in range(12)]
  random.seed(20702); armor_second=[db.get_random_loot_armor_type() for _ in range(12)]
  if armor_first!=armor_second or not set(armor_first)<=ARMOR_TYPES: fail("armor-type deterministic contract failed")
  checks+=2

  for slot,rarity,hands,profile in (("main_hand","rare",2,"staff_2h"),("off_hand","uncommon",1,"shield")):
   name=db.get_dynamic_weapon_name(slot,rarity,hands,profile)
   if not isinstance(name,str) or not name.strip(): fail("dynamic weapon name contract failed")
   random.seed(20703); stats1=db.generate_dynamic_equipment_stats(slot,8,rarity,hands,profile)
   random.seed(20703); stats2=db.generate_dynamic_equipment_stats(slot,8,rarity,hands,profile)
   if stats1!=stats2 or not isinstance(stats1,dict): fail("dynamic stats deterministic contract failed")
   if not STAT_KEYS.issubset(stats1): fail("dynamic stats keys missing")
   if any(int(stats1[k] or 0)<0 for k in STAT_KEYS): fail("dynamic stats negative value")
   checks+=2

  profile_stats={"bonus_str":2,"bonus_dex":1,"bonus_int":3,"bonus_wis":2,"bonus_sta":4,"pdef":5,"mdef":6}
  before_budget=db.get_existing_primary_stat_budget(profile_stats)
  profile=db.ARMOR_PRIMARY_STAT_PROFILES["cloth"]
  expected_primary=max(1,int(round(before_budget*float(profile.get("main_multiplier",1.0)))))
  expected_secondary=max(1,int(round(before_budget*float(profile.get("secondary_multiplier",0.5))))) if before_budget>=2 else 0
  expected_profile_budget=expected_primary+expected_secondary
  random.seed(20704); profiled1=db.apply_armor_type_primary_stat_profile_to_stats(copy.deepcopy(profile_stats),"cloth")
  random.seed(20704); profiled2=db.apply_armor_type_primary_stat_profile_to_stats(copy.deepcopy(profile_stats),"cloth")
  after_budget=db.get_existing_primary_stat_budget(profiled1)
  if profiled1!=profiled2: fail("armor primary-stat profile is not deterministic with fixed seed")
  if after_budget!=expected_profile_budget: fail(f"armor primary-stat profile budget mismatch: expected {expected_profile_budget}, got {after_budget}")
  if int(profiled1.get("pdef",0) or 0)!=5 or int(profiled1.get("mdef",0) or 0)!=6: fail("armor primary-stat profile changed defense fields")
  checks+=1

  # Isolated mutation fixture. create_user is the current public registration contract.
  db.create_user(TEST_USER_ID)
  if not db.conn.execute("SELECT 1 FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone(): fail("fixture user creation failed")
  try: db.conn.execute("UPDATE users SET bag_slots=40, character_class='mage' WHERE user_id=?",(TEST_USER_ID,)); db.conn.commit()
  except Exception: pass

  random.seed(20705)
  generated=db.create_generated_equipment_item(TEST_USER_ID,8,"rare",class_aware_chance=0.0)
  item_contract(generated); checks+=1
  random.seed(20706)
  generated_slot=db.create_generated_equipment_item_for_slot(TEST_USER_ID,8,"uncommon","main_hand","staff_2h")
  _item,_inventory,slot=item_contract(generated_slot)
  if slot!="main_hand": fail("slot-specific generation contract failed")
  checks+=1
 finally:
  random.setstate(random_state)
  cleanup_fixture()

 if db.conn.execute("SELECT COUNT(*) FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone()[0]: fail("fixture user cleanup failed")
 real_after=[tuple(r) for r in db.conn.execute("SELECT user_id FROM users WHERE user_id>=0 ORDER BY user_id").fetchall()]
 if real_before!=real_after: fail("real user set changed")
 print("[OK] dynamic equipment and repair-read contracts")
 print(f"- deterministic/helper checks: {checks}")
 print(f"- repair-read comparisons: {repair_comparisons}")
 print("- generated item contracts: 2")
 print("- random state restored: OK")
 print("- isolated fixture cleanup: OK")
 print("- real user mutations: 0")
if __name__=="__main__": main()
'''

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"systems"/"equipment_system.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def main():
 r=root(); target=r/"tools"/TOOL_NAME; backup=None
 if target.exists() and target.read_text(encoding="utf-8-sig")!=TOOL:
  b=r/"backup"; b.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); backup=b/f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"; shutil.copy2(target,backup)
 target.write_text(TOOL,encoding="utf-8")
 try:
  py_compile.compile(str(target),doraise=True)
  result=subprocess.run([sys.executable,str(target)],cwd=r)
  if result.returncode: raise RuntimeError(f"contract test exit code {result.returncode}")
 except Exception as e:
  if backup: shutil.copy2(backup,target)
  elif target.exists(): target.unlink()
  fail(f"Контрактні тести не пройдено; встановлення відкочено: {e}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print(f"✅ Створено: tools/{TOOL_NAME}")
 print("✅ Random state відновлено, ізольовані записи видалено.")
 print("✅ Реальні користувачі не змінені.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r) if backup else 'не потрібні - новий файл'}")
 print("Перевірки:")
 print(f"   python ./tools/{TOOL_NAME}")
 print("   python ./tools/smoke_test_equipment_readonly_core.py")
 print("   python ./tools/smoke_test_weapon_damage_contracts.py")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
