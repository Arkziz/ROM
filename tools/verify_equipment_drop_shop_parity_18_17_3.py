#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,random,sqlite3,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
DB=R/"game.db";REPORT=R/"reports/stage_18_17_3_equipment_drop_shop_parity.json";MD=R/"MD/STAGE_18_17_3_EQUIPMENT_DROP_SHOP_PARITY.md"
GEN=R/"db_modules/generated_equipment.py";SHOP=R/"db_modules/shop.py";POLICY=R/"data/equipment_stat_policy.py";DYNAMIC=R/"systems/dynamic_equipment_system.py"
from data.equipment_stat_policy import CLASS_ARMOR_TYPES,CLASS_MAIN_HAND_SUBTYPES,CLASS_OFF_HAND_SUBTYPES,PRIMARY_STATS,get_allowed_equipment_stats,get_equipment_stat_weights,redistribute_primary_stat_budget,validate_equipment_stat_policy
CLASSES=("warrior","knight","scout","rogue","mage","priest")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source(p):return p.read_text(encoding="utf-8-sig")
def fn(tree,name):
 x=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
 if len(x)!=1:raise RuntimeError(f"{name} count={len(x)}")
 return x[0]
def calls(owner,name):
 return [n for n in ast.walk(owner) if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id==name) or (isinstance(n.func,ast.Attribute) and n.func.attr==name))]
def choose(profile):return random.choices([s for s,_ in profile],weights=[w for _,w in profile],k=1)[0]
def deterministic_matrix():
 rows=[]
 subtype={"warrior":"sword_1h","knight":"sword_1h","scout":"bow_2h","rogue":"dagger_1h","mage":"wand_1h","priest":"wand_1h"}
 for cls in CLASSES:
  routes=[("drop_weapon","weapon",subtype[cls]),("shop_weapon","weapon",subtype[cls]),("drop_armor","armor",""),("shop_armor","armor",""),("drop_necklace","jewelry",""),("shop_necklace","jewelry",""),("drop_ring","jewelry",""),("shop_ring","jewelry","")]
  if CLASS_OFF_HAND_SUBTYPES[cls]:
   off=CLASS_OFF_HAND_SUBTYPES[cls][0];routes += [("drop_off_hand","off_hand",off),("shop_off_hand","off_hand",off)]
  for route,kind,sub in routes:
   allowed=set(get_allowed_equipment_stats(cls,kind,item_subtype=sub));counts=Counter()
   for seed in range(200):
    base={"bonus_str":7,"bonus_dex":5,"bonus_int":3,"bonus_wis":2,"bonus_sta":4,"pdef":11,"mdef":13}
    random.seed(seed);result=redistribute_primary_stat_budget(base,cls,kind,item_subtype=sub,chooser=choose)
    assert sum(result["bonus_"+s] for s in PRIMARY_STATS)==21
    assert all(result["bonus_"+s]==0 for s in set(PRIMARY_STATS)-allowed)
    assert result["pdef"]==11 and result["mdef"]==13
    counts.update(s for s in allowed if result["bonus_"+s]>0)
   configured={s for s,w in get_equipment_stat_weights(cls,kind,item_subtype=sub) if w>0}
   if set(counts)!=configured:raise RuntimeError(f"coverage missing {cls}:{route}: {configured-set(counts)}")
   rows.append({"class":cls,"route":route,"kind":kind,"subtype":sub,"allowed":sorted(allowed),"observed":dict(counts)})
 return rows
def dbcheck():
 before=sha(DB);c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:
  c.execute("PRAGMA query_only=ON");out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def main():
 assert validate_equipment_stat_policy()==()
 texts={p.name:source(p) for p in (GEN,SHOP,POLICY,DYNAMIC)}
 for p in (GEN,SHOP,POLICY,DYNAMIC):ast.parse(texts[p.name])
 gt=ast.parse(texts[GEN.name]);st=ast.parse(texts[SHOP.name]);dt=ast.parse(texts[DYNAMIC.name])
 drop=fn(gt,"create_generated_equipment_item");forced=fn(gt,"create_generated_equipment_item_for_slot");preview=fn(st,"create_common_equipment_shop_preview");purchase=fn(st,"purchase_shop_preview_item")
 assert len(calls(drop,"redistribute_primary_stat_budget"))==1
 assert len(calls(forced,"redistribute_primary_stat_budget"))==1
 assert len(calls(preview,"redistribute_primary_stat_budget"))==1
 assert len(calls(purchase,"promote_shop_preview_item"))==1
 assert not calls(purchase,"redistribute_primary_stat_budget")
 assert not calls(purchase,"generate_dynamic_equipment_stats")
 assert not calls(purchase,"random") and not calls(purchase,"choices")
 assert any(isinstance(n,ast.Import) and any(a.name=="random" for a in n.names) for n in st.body)
 # Purchase promotion must preserve preview snapshot and must not reroll stats.
 purchase_text=ast.get_source_segment(texts[SHOP.name],purchase) or ""
 assert "promote_shop_preview_item" in purchase_text and "DELETE FROM items" in purchase_text
 # Creation ownership remains in db_modules; dynamic module has no item creators.
 dnames={n.name for n in dt.body if isinstance(n,ast.FunctionDef)}
 assert "create_generated_equipment_item" not in dnames and "create_generated_equipment_item_for_slot" not in dnames
 matrix=deterministic_matrix();db=dbcheck()
 if db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"]:raise RuntimeError("DB invariant failed")
 report={"stage":"18.17.3","status":"PASS","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"routes":{"class_aware_drop_policy_calls":1,"forced_slot_policy_calls":1,"base_shop_preview_policy_calls":1,"purchase_policy_calls":0,"purchase_promotions":1,"purchase_reroll":False},"class_armor_types":dict(CLASS_ARMOR_TYPES),"matrix":matrix,"matrix_rows":len(matrix),"samples_per_row":200,"database":db,"compatibility":{"item_creation_owner":"db_modules/generated_equipment.py","dynamic_module_creates_items":False,"calculation_duplicates_present":True,"consolidation":"deferred to a separate source-faithful patch after import-surface audit"},"accepted_manual_checks":["Stage 18.17.2: class-aware mob drop flow completed without traceback","Stage 18.17.2a: base shop previews verified with multiple classes","Shop preview and purchased item flow works after random import recovery"],"next_stage":"18.17.4 dynamic equipment compatibility consolidation read-only/import-surface audit"}
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 lines=["# Stage 18.17.3: Equipment Drop and Shop Parity","",f"**Status:** {report['status']}","**Production mutation:** none","", "## Verified contract","","- Class-aware mob drops, forced-slot generation and base-shop previews use the same canonical policy.","- Purchase promotion does not regenerate or reroll the preview snapshot.","- All six classes, armor, weapon, jewelry and supported off-hand routes are covered deterministically.","- Primary-stat budget and PDEF/MDEF are preserved.","- Existing generated items and game.db are unchanged.","", "## Compatibility decision","","- Item creation remains owned by `db_modules/generated_equipment.py`.","- `systems/dynamic_equipment_system.py` does not create items.","- Duplicate calculation helpers remain and require a separate import-surface audit before consolidation.","", "## Database safety","",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","matrix_rows":len(matrix),"samples":len(matrix)*200,"purchase_reroll":False,"db_unchanged":True,"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
