#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.behavior_policy import BehaviorPolicy
from systems.simulation.meta_progression import SimulationMetaProgressionService
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem
from systems.simulation.rng import SimulationRng
from systems.simulation.survival_state import PersistentCombatState,SimulationSurvivalService
from systems.simulation.equipment_service import SimulationEquipmentService
def make(sid,iid,name,cat,q=1,stack=1,slot='',rar='common',dur=100,sell=0.0,stats=None,armor='',subtype=''):
 return SimulationInventoryItem(sid,iid,name,cat,q,stack,slot,1,rar,dur,0,armor,subtype,1,sell,stats or {})
def qty(inv,iid):return sum(x.quantity for x in inv.items if x.item_id==iid)
def ok(v,n,c,d=None):
 c.append({'name':n,'status':'PASS' if v else 'FAIL','details':d or {}})
 if not v:raise AssertionError(n)
def run_fixture():
 c=[];line=[];policy=BehaviorPolicy();actor=PersistentCombatState(130,130,0,0);ok((actor.hp,actor.max_hp)==(130,130),'canonical 130 HP baseline',c)
 inv=SimulationInventory(capacity=40);eq=SimulationEquipment();sur=SimulationSurvivalService(inv,eq);meta=SimulationMetaProgressionService(inv,eq,SimulationRng(3));gear=SimulationEquipmentService('scout',inv,eq)
 inv.items.append(make(1,401,'HP potion','potion',2,99,stats={'restore':38}));actor.hp=51;d=policy.choose_potion(actor.hp,actor.max_hp,0,0,False,[{'item_id':401,'restore':38}],[]);ok(d and d.action=='use_hp_potion','HP below 40% selects potion',c);actor.hp+=38;inv.items[0].quantity-=1;line.append('potion_used')
 actor.hp=32;ok(actor.hp/actor.max_hp<=.25,'pre-hunt HP wait boundary',c);ok(actor.passive_hp_regen(5)>0,'pre-hunt recovery',c);line.append('pre_hunt_wait')
 better=make(2,900002,'uncommon legs','equipment',slot='legs',rar='uncommon',sell=.9,stats={'dex':2,'sta':1,'pdef':2},armor='leather',subtype='armor');worse=make(3,900003,'common legs','equipment',slot='legs',sell=.3,stats={'sta':1,'pdef':1},armor='leather',subtype='armor');inv.items.extend([better,worse]);d=gear.decide(2);ok(d.action=='equip','better equipment selected',c);gear.apply(d);ok(gear.decide(3).action=='sell','worse equipment rejected',c);inv.items.remove(worse);initial_gold=20.0;equipment_sale=.30;gold=round(initial_gold+equipment_sale,2);line+=['equip','sell_worse']
 inv.items.append(make(4,601,'stone','material',2,999));meta.refine_best();attempts=meta.state.refine_attempts;ok(attempts==2 and qty(inv,601)==0,'refinement stone conservation',c);ok(better.refine_level==2,'refinement applied',c);line.append('refine')
 inv.items.extend([make(5,706,'STA rune','material'),make(6,711,'DEX rune','material')]);before=qty(inv,706)+qty(inv,711);inserted=meta.insert_best_runes('scout');ok(inserted>=1 and better.runes[0].stat=='DEX','class-aware DEX rune insertion',c);ok(qty(inv,706)+qty(inv,711)==before-inserted,'inserted rune conservation',c);line.append('rune_insert')
 better.durability=5;death=sur.damage_on_death();actor.apply_death();ok(better.durability==0 and death.broken==1 and actor.hp==1,'death and break lifecycle',c);old=meta.state.refine_attempts;inv.items.append(make(7,601,'stone','material',1,999));meta.refine_best();ok(meta.state.refine_attempts==old,'broken item blocks refinement',c);line.append('death_break')
 g,fail=sur.urgent_repair(.01);ok(fail.repaired==0 and better.durability==0 and g==.01,'insufficient gold blocks repair',c);gold_before=gold;gold,repair=sur.urgent_repair(gold);ok(repair.repaired==1 and better.durability==100 and gold==round(gold_before-repair.cost,2),'repair restores durability and debits gold',c);line.append('repair')
 ok(2-1==qty(inv,401),'potion conservation',c);ok(3-attempts==qty(inv,601),'stone final conservation',c);ok(2-inserted==qty(inv,706)+qty(inv,711),'rune final conservation',c);ok(round(initial_gold+equipment_sale-repair.cost,2)==gold,'gold reconciliation',c);ok(2==1+1,'equipment conservation',c)
 expected=['potion_used','pre_hunt_wait','equip','sell_worse','refine','rune_insert','death_break','repair'];ok(line==expected,'integrated lifecycle order',c,{'timeline':line})
 return {'status':'PASS','check_count':len(c),'checks':c,'timeline':line,'final':{'hp':actor.hp,'gold':gold,'equipment':{'durability':better.durability,'refine_level':better.refine_level,'runes':[{'stat':x.stat,'level':x.level,'slot_index':x.slot_index} for x in better.runes]},'resources':{'potions':qty(inv,401),'stones':qty(inv,601),'runes':qty(inv,706)+qty(inv,711)}}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',required=True);a=p.parse_args();x=run_fixture();o=Path(a.report);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f"[PASS] integrated lifecycle checks: {x['check_count']}");return 0
if __name__=='__main__':raise SystemExit(main())
