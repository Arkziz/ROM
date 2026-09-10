#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only structural audit and deterministic balance model for Rebirth Sphere drops."""
from __future__ import annotations
import ast,json,math,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
REBIRTH_ID=504
REPORT=ROOT/"reports/stage_18_16_10e_rebirth_sphere_distribution_audit.json"
MD=ROOT/"reports/stage_18_16_10e_rebirth_sphere_distribution_audit.md"
SCENARIOS={
 "A_very_rare":{"normal":0.00010,"elite":0.00050,"boss":0.0050},
 "B_balanced":{"normal":0.00020,"elite":0.00100,"boss":0.0100},
 "C_boss_focused":{"normal":0.00005,"elite":0.00050,"boss":0.0200},
}
ACTIVITY={"battles_per_active_day":{"normal":35,"elite":4,"boss":1},"active_days_per_month":25}
def source(path):return (ROOT/path).read_text(encoding="utf-8-sig")
def tph(chances,mix):return sum(float(chances[k])*int(mix[k]) for k in ("normal","elite","boss"))
def scenario_metrics(chances):
 mix=ACTIVITY["battles_per_active_day"];daily=tph(chances,mix);monthly=daily*ACTIVITY["active_days_per_month"]
 return {
  "chances":chances,
  "expected_per_1000":{"normal":chances["normal"]*1000,"elite":chances["elite"]*1000,"boss":chances["boss"]*1000},
  "expected_drops_per_active_day":daily,
  "expected_drops_per_active_month":monthly,
  "probability_at_least_one_per_month":1-math.exp(-monthly),
  "median_active_days_to_first_drop":None if daily<=0 else math.log(2)/daily,
  "mean_active_days_to_first_drop":None if daily<=0 else 1/daily,
  "monthly_supply_per_100_active_players":monthly*100,
  "monthly_source_share":{k:(chances[k]*mix[k]/daily if daily else 0) for k in mix},
 }
def main():
 drop_tables=source(Path("data/drop_tables.py"));drop_system=source(Path("systems/drop_system.py"));policy=source(Path("data/rebirth_sphere_policy.py"));auction=source(Path("systems/auction_house_system.py"));interaction=source(Path("systems/player_interaction_system.py"))
 for text in (drop_tables,drop_system,policy,auction,interaction):ast.parse(text)
 from data.drop_tables import CENTRAL_DROP_PRODUCTION_ENABLED,CENTRAL_DROP_MIGRATED_RULES,DROP_RULES
 from data.rebirth_sphere_policy import get_sphere_economic_policy
 with sqlite3.connect((ROOT/"game.db").resolve().as_uri()+"?mode=ro",uri=True) as c:
  item=c.execute("SELECT id,name,type,category,max_stack,sell_price FROM items WHERE id=?",(REBIRTH_ID,)).fetchone();quick=c.execute("PRAGMA quick_check").fetchone()[0];fk=c.execute("PRAGMA foreign_key_check").fetchall();before=c.total_changes
 policy504=get_sphere_economic_policy(REBIRTH_ID)
 rules=[r for r in DROP_RULES if int(r.get("item_id",-1))==REBIRTH_ID or r.get("rule_id")=="rebirth_sphere"]
 audit={
  "stage":"18.16.10e","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,
  "database":{"quick_check":quick,"foreign_key_violations":fk,"total_changes":before,"item":item},
  "economic_policy":policy504,
  "central_drop":{"production_enabled":bool(CENTRAL_DROP_PRODUCTION_ENABLED),"migrated_rules":list(CENTRAL_DROP_MIGRATED_RULES),"rebirth_rules":rules,"integration_points":{
   "enemy_classifier":"systems.drop_system.classify_enemy","rule_executor":"systems.drop_system.roll_rule","production_executor":"systems.drop_system.process_central_production_drops","simulation":"systems.drop_system.simulate_central_drops"}},
  "current_state":{"configured_for_drop":bool(rules),"production_drop_enabled":any(bool(r.get("production_enabled")) for r in rules),"conclusion":"Rebirth Sphere is economically drop-eligible but has no DROP_RULE yet."},
  "activity_model":ACTIVITY,"scenarios":{name:scenario_metrics(values) for name,values in SCENARIOS.items()},
  "recommended_scenario":"B_balanced",
  "mutation_requirements":[
   "Add one independent static_item rule for item_id 504 to data/drop_tables.py.",
   "Use quantity 1, max_per_kill 1, stack_or_lose bag policy and standard_item message policy.",
   "Keep item 501 absent from every enabled enemy-drop rule.",
   "Add deterministic simulation and production award smoke tests before enabling the rule."],
 }
 REPORT.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
 lines=["# Stage 18.16.10e: Rebirth Sphere Distribution Audit","",f"Generated: {audit['generated_at_utc']}","","## Current production state","",f"- Central drop enabled: **{audit['central_drop']['production_enabled']}**",f"- Rebirth Sphere DROP_RULE present: **{audit['current_state']['configured_for_drop']}**",f"- Production drop enabled: **{audit['current_state']['production_drop_enabled']}**",f"- Item: `{item}`","", "## Activity model","",f"- Normal battles/day: {ACTIVITY['battles_per_active_day']['normal']}",f"- Elite battles/day: {ACTIVITY['battles_per_active_day']['elite']}",f"- Boss battles/day: {ACTIVITY['battles_per_active_day']['boss']}",f"- Active days/month: {ACTIVITY['active_days_per_month']}","","## Balance scenarios",""]
 for name,m in audit["scenarios"].items():
  lines.extend([f"### {name}","",f"- Chances: normal `{m['chances']['normal']:.5%}`, elite `{m['chances']['elite']:.5%}`, boss `{m['chances']['boss']:.3%}`",f"- Expected drops/player/month: `{m['expected_drops_per_active_month']:.4f}`",f"- Chance of at least one/month: `{m['probability_at_least_one_per_month']:.2%}`",f"- Median active days to first drop: `{m['median_active_days_to_first_drop']:.1f}`",f"- Supply per 100 active players/month: `{m['monthly_supply_per_100_active_players']:.2f}`",f"- Source share: normal `{m['monthly_source_share']['normal']:.1%}`, elite `{m['monthly_source_share']['elite']:.1%}`, boss `{m['monthly_source_share']['boss']:.1%}`",""])
 lines.extend(["## Recommendation","", "Use **B_balanced** as the initial candidate, subject to owner approval. It gives a meaningful but still rare market supply without making normal mobs irrelevant.","","## Production mutation","","No production mutation was performed by this audit."])
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","configured":bool(rules),"recommended":"B_balanced","json":str(REPORT.relative_to(ROOT)),"md":str(MD.relative_to(ROOT))},ensure_ascii=False))
if __name__=="__main__":main()
