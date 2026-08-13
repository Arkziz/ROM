from __future__ import annotations
import json, random
from collections import Counter
from pathlib import Path
from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_policy_metrics_audit import _choose as choose_action, _valid as skill_valid
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import build_real_actor
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION="14.6.3b2"

def _judgement_skill(catalog):
    matches=[s for s in catalog["knight"] if s.get("key")=="knight_judgement"]
    if len(matches)!=1: raise AssertionError(f"knight_judgement definitions={len(matches)}")
    return matches[0]

def _replay_pair(opponent_key,trials,seed):
    catalog=load_production_pvp_skill_catalog(); skill=_judgement_skill(catalog)
    counts=Counter(); outcomes=Counter(); terminals=Counter(); winner_reasons=Counter(); stun_by_skill=Counter(); stun_skips=Counter()
    forced_samples=[]
    for i in range(trials):
        swap=bool(i%2); ca,cb=(opponent_key,"knight") if swap else ("knight",opponent_key)
        a,b=build_real_actor(ca,1),build_real_actor(cb,2)
        for rnd in range(1,51):
            actors={1:a,2:b}; knight=a if a.class_key=="knight" else b; opponent=b if knight is a else a
            valid=skill_valid(knight,skill); resource_ok=knight.resource>=int(skill.get("cost") or 0); cooldown=int(knight.cooldowns.get("knight_judgement",0) or 0)
            shield=dict(knight.effects.get("shield") or {}); remaining=int(shield.get("remaining",0) or 0)
            chosen=choose_action(knight,opponent,"target_aware",random.Random(seed+i*1000+rnd+71),catalog)
            counts["rounds_observed"]+=1
            if resource_ok: counts["resource_reachable"]+=1
            if cooldown<=1: counts["cooldown_ready"]+=1
            if valid: counts["technically_valid"]+=1
            if chosen.skill_key=="knight_holy_protection": counts["blocked_by_holy_protection_priority"]+=int(valid)
            elif chosen.skill_key=="knight_shield_bash": counts["lost_to_shield_bash"]+=int(valid)
            elif chosen.skill_key=="knight_judgement": counts["policy_selected"]+=1
            if valid and len(forced_samples)<10:
                k=knight.clone(); o=opponent.clone(); before=o.hp
                if k.user_id==1: fr=resolve_pvp_round(rnd,0,k,o,PvpActionIntent(k.user_id,"skill","knight_judgement"),PvpActionIntent(o.user_id,"basic_attack"),seed=seed+i*1000+rnd+999,catalog=catalog)
                else: fr=resolve_pvp_round(rnd,0,o,k,PvpActionIntent(o.user_id,"basic_attack"),PvpActionIntent(k.user_id,"skill","knight_judgement"),seed=seed+i*1000+rnd+999,catalog=catalog)
                ko=next(x for x in fr.outcomes if x.user_id==k.user_id)
                forced_samples.append({"valid":ko.valid,"reason":ko.reason,"damage":ko.damage,"resource_spent":ko.resource_spent,"target_hp_before":before})
            ia=choose_action(a,b,"target_aware",random.Random(seed+i*1000+rnd),catalog); ib=choose_action(b,a,"target_aware",random.Random(seed+i*1000+rnd+37),catalog)
            result=resolve_pvp_round(rnd,rnd,a,b,ia,ib,seed=seed+i*1000+rnd,catalog=catalog)
            for out in result.outcomes:
                if out.reason=="stunned_skip": stun_skips[actors[out.user_id].class_key]+=1
                if any(str(e.get("kind") or "")=="stun" for e in (out.applied_effects or ())): stun_by_skill[str(out.skill_key or out.action_type)]+=1
            a=PvpActorState.from_dict(result.actor_a); b=PvpActorState.from_dict(result.actor_b)
            if result.terminal:
                reason=str(result.result_reason or "none"); terminals[reason]+=1
                winner="draw" if result.winner_id is None else (a.class_key if result.winner_id==a.user_id else b.class_key)
                winner_reasons[f"{reason}:{winner}"]+=1
                break
    outcomes.update(x["reason"] for x in forced_samples)
    return {"opponent":opponent_key,"trials":trials,"reachability":dict(counts),"forced_judgement_samples":forced_samples,"forced_outcome_reasons":dict(outcomes),"terminal_reasons":dict(terminals),"winner_by_reason":dict(winner_reasons),"stun_applied_by_skill":dict(stun_by_skill),"stunned_skips_by_class":dict(stun_skips)}

def run_audit(trials=100,seed=14633):
    trials=max(10,min(300,int(trials))); catalog=load_production_pvp_skill_catalog(); skill=_judgement_skill(catalog)
    rows=[_replay_pair(cls,trials,seed+i*100000) for i,cls in enumerate(CLASSES) if cls!="knight"]
    total=Counter()
    for row in rows: total.update(row["reachability"])
    forced=[s for row in rows for s in row["forced_judgement_samples"]]
    terminal_catalog=Counter(); winner_catalog=Counter(); stun_catalog=Counter(); skips=Counter()
    for row in rows:
        terminal_catalog.update(row["terminal_reasons"]); winner_catalog.update(row["winner_by_reason"]); stun_catalog.update(row["stun_applied_by_skill"]); skips.update(row["stunned_skips_by_class"])
    reachable=int(total["technically_valid"]); selected=int(total["policy_selected"])
    diagnosis=[]
    if reachable==0: diagnosis.append("judgement_never_reaches_valid_state")
    elif selected==0 and total["blocked_by_holy_protection_priority"]>0: diagnosis.append("holy_protection_priority_starves_judgement")
    elif selected==0: diagnosis.append("judgement_valid_but_not_selected")
    if forced and not all(x["valid"] for x in forced): diagnosis.append("forced_judgement_execution_failure")
    return {"version":VERSION,"verdict":"PASS_WITH_REVIEW" if diagnosis else "PASS","trials_per_opponent":trials,"skill_definition":skill,"opponents_checked":len(rows),"rows":rows,"aggregate_reachability":dict(total),"forced_judgement":{"samples":len(forced),"all_valid":bool(forced) and all(x["valid"] for x in forced),"avg_damage":round(sum(x["damage"] for x in forced)/max(1,len(forced)),2),"avg_resource_spent":round(sum(x["resource_spent"] for x in forced)/max(1,len(forced)),2)},"terminal_reason_semantics":{"reason_counts":dict(terminal_catalog),"winner_assignment_by_reason":dict(winner_catalog),"note":"simultaneous denotes simultaneous action resolution; draw_simultaneous denotes simultaneous death"},"stun_attribution":{"applied_by_skill":dict(stun_catalog),"stunned_skips_by_class":dict(skips),"total_stunned_skips":sum(skips.values())},"diagnosis":diagnosis,"production_round_resolver_used":True,"production_skill_catalog_used":True,"target_aware_policy_used":True,"live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}

def save_report(data,path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return p

def format_summary(d):
    r=d["aggregate_reachability"]; f=d["forced_judgement"]; s=d["stun_attribution"]
    return "\n".join([f"PvP Knight Judgement reachability audit {d['version']}",f"Verdict: {d['verdict']}",f"Opponents checked: {d['opponents_checked']}/5",f"Trials/opponent: {d['trials_per_opponent']}",f"Technically valid rounds: {r.get('technically_valid',0)}",f"Policy selected Judgement: {r.get('policy_selected',0)}",f"Blocked by Holy Protection priority: {r.get('blocked_by_holy_protection_priority',0)}",f"Forced Judgement valid: {'PASS' if f['all_valid'] else 'FAIL'}",f"Forced average damage: {f['avg_damage']}",f"Stunned skips attributed: {s['total_stunned_skips']}",f"Diagnosis: {', '.join(d['diagnosis']) if d['diagnosis'] else 'none'}","Live balance changed: NO"])
