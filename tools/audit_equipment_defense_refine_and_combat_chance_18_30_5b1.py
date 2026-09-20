#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json,sys
from dataclasses import asdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
OUT=R/"reports"/"simulation"/"stage_18_30_5b1_equipment_defense_refine_combat_chance_audit.json"
FILES=("data/player_hp.py","data/player_combat_chances.py","data/defense_policy.py","systems/stat_system.py","systems/refine_system.py","systems/combat_system.py","systems/simulation/canonical_rules.py","systems/simulation/combat_actor_stats.py","systems/simulation/pve_battle.py","systems/simulation/models.py")
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def make_item(item_id,slot,stats,durability=100,refine=0,runes=None,rarity="common"):
 from systems.simulation.models import SimulationInventoryItem
 x=SimulationInventoryItem(item_id,910000+item_id,f"fixture-{item_id}","equipment",1,1,slot,1,rarity,durability=durability,refine_level=refine,stats=dict(stats));x.runes=list(runes or []);return x
def snapshot(item=None):
 from systems.simulation.combat_actor_stats import build_combat_stat_snapshot
 from systems.simulation.models import SimulationEquipment,SimulationInventory
 inv=SimulationInventory();eq=SimulationEquipment()
 if item:inv.items.append(item);eq.slots[item.slot_key]=item.simulation_item_id
 return build_combat_stat_snapshot("scout",1,inv,eq)
def expected(item=None):
 from data.player_hp import calculate_base_max_hp
 from systems.refine_system import apply_weapon_refine_to_damage,get_armor_refine_hp_bonus_percent
 from systems.stat_system import calculate_magical_attack,calculate_max_mp,calculate_physical_attack,calculate_physical_defense,calculate_magical_defense
 stats={"str":10,"dex":10,"int":10,"wis":10,"sta":10};pdef=mdef=0;amin=amax=0;armor_pct=0.0;active=bool(item and int(item.durability or 0)>0)
 if active:
  for k in stats:stats[k]+=int(item.stats.get(k,item.stats.get(f"bonus_{k}",0)) or 0)
  for rune in item.runes:
   k=str(rune.stat).lower();stats[k]=stats.get(k,0)+int(rune.level)
  pdef=int(item.stats.get("pdef",0) or 0);mdef=int(item.stats.get("mdef",0) or 0)
  if item.slot_key in {"helmet","shoulders","chest","gloves","legs","boots"}:armor_pct=float(get_armor_refine_hp_bonus_percent(item.refine_level,item.rarity) or 0)
  if item.slot_key=="main_hand":
   amin=int(item.stats.get("weapon_min_damage",0) or 0);amax=int(item.stats.get("weapon_max_damage",0) or 0);amin,amax=apply_weapon_refine_to_damage(amin,amax,item.refine_level)
 base=calculate_base_max_hp(1,stats["sta"]);hp=max(1,int(round(base*(1+armor_pct/100))))
 kw={"strength":stats["str"],"dexterity":stats["dex"],"intelligence":stats["int"],"wisdom":stats["wis"],"stamina":stats["sta"]}
 return {"str":stats["str"],"dex":stats["dex"],"intelligence":stats["int"],"wis":stats["wis"],"sta":stats["sta"],"max_hp":hp,"max_mp":calculate_max_mp("scout",level=1,intelligence=stats["int"],wisdom=stats["wis"]),"attack":calculate_physical_attack("scout",**kw),"magic_attack":calculate_magical_attack("scout",**kw),"pdef":calculate_physical_defense(equipment_pdef=pdef,stamina=stats["sta"]),"mdef":calculate_magical_defense(equipment_mdef=mdef,wisdom=stats["wis"]),"weapon_min_damage":amin,"weapon_max_damage":amax,"armor_refine_hp_percent":armor_pct}
def row(label,item=None):
 s=snapshot(item);e=expected(item);sd=asdict(s);keys=("str","dex","intelligence","wis","sta","max_hp","max_mp","attack","magic_attack","pdef","mdef","weapon_min_damage","weapon_max_damage");cmp={k:{"simulation":sd[k],"canonical":e[k],"delta":sd[k]-e[k],"parity":"PASS" if sd[k]==e[k] else "FAIL"} for k in keys};return {"scenario":label,"simulation":sd,"canonical":e,"comparison":cmp,"failed_stats":[k for k,v in cmp.items() if v["parity"]=="FAIL"]}
def chance_contract():
 from systems.simulation.canonical_rules import rule_manifest
 manifest={x["name"]:x for x in rule_manifest()}
 src=(R/"systems"/"simulation"/"pve_battle.py").read_text(encoding="utf-8");tree=ast.parse(src);calls=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="call_rule":calls.append({"rule":ast.literal_eval(n.args[0]) if n.args and isinstance(n.args[0],ast.Constant) else ast.unparse(n.args[0]),"line":n.lineno})
 return {"manifest":{k:manifest.get(k) for k in ("player_attack","mob_attack","physical_crit_chance","magical_crit_chance","dodge_chance")},"pve_battle_call_rule_calls":calls,"player_attack_used":any(x["rule"]=="player_attack" for x in calls),"mob_attack_used":any(x["rule"]=="mob_attack" for x in calls)}
def main():
 from systems.simulation.models import SimulationRuneSocket
 scenarios=[row("empty"),row("sta_equipment",make_item(1,"chest",{"sta":2,"pdef":3,"mdef":1})),row("sta_rune",make_item(2,"chest",{"pdef":1},runes=[SimulationRuneSocket(0,1001,"sta",1)])),row("refined_armor",make_item(3,"chest",{"sta":1,"pdef":2},refine=2)),row("refined_weapon",make_item(4,"main_hand",{"dex":2,"weapon_min_damage":10,"weapon_max_damage":20},refine=3)),row("zero_durability_armor",make_item(5,"chest",{"sta":9,"pdef":99,"mdef":99},durability=0,refine=6,runes=[SimulationRuneSocket(0,1002,"sta",5)])),row("zero_durability_weapon",make_item(6,"main_hand",{"dex":9,"weapon_min_damage":100,"weapon_max_damage":200},durability=0,refine=10))]
 failed=sorted({k for r in scenarios for k in r["failed_stats"]});chance=chance_contract();findings=[f"SIMULATION_{k.upper()}_PARITY_FAILURE" for k in failed]
 if not(chance["player_attack_used"] and chance["mob_attack_used"]):findings.append("SIMULATION_BATTLE_DOES_NOT_USE_CANONICAL_ATTACK_RULES")
 corrected={"pdef_mdef_previous_false_positive":all(k not in failed for k in ("pdef","mdef")),"armor_refine_previous_false_positive":scenarios[3]["comparison"]["max_hp"]["delta"]==40,"combat_chances_delegated_through_canonical_attack_rules":chance["player_attack_used"] and chance["mob_attack_used"]}
 payload={"stage":"18.30.5b1","mode":"read-only","verdict":"FAIL" if findings else "PASS","corrected_equipment_refine_durability_scenarios":scenarios,"combat_chance_contract":chance,"corrected_conclusions":corrected,"failed_stats":failed,"findings":findings,"recommended_next_patch":"patch_18_30_5c_restore_canonical_player_stat_parity.py","files_sha256":{x:sha(R/x) for x in FILES}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"[PASS] corrected scenarios: {len(scenarios)}");print(f"[INFO] failed stats: {', '.join(failed) if failed else 'none'}");print(f"[INFO] combat chance delegation: {'PASS' if corrected['combat_chances_delegated_through_canonical_attack_rules'] else 'FAIL'}");print(f"[REPORT] {OUT.relative_to(R)}")
if __name__=="__main__":main()
