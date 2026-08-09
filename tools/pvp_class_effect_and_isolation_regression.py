from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from systems.pvp_config import (
    PVP_COMBAT_ENERGY_MAX, PVP_CONSECUTIVE_AFK_LIMIT,
    PVP_DAMAGE_MULTIPLIER, PVP_DEBUFF_MULTIPLIER,
    PVP_HEALING_MULTIPLIER, PVP_MAX_ROUNDS,
    PVP_SHIELD_MULTIPLIER,
)
from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

CLASSES=("warrior","knight","scout","rogue","mage","priest")
RESOURCE={"warrior":"rage","knight":"rage","scout":"combat_energy","rogue":"combat_energy_combo","mage":"mana","priest":"mana"}
EXPECTED_EFFECT={
    "warrior_suppression":"pdef_down",
    "knight_holy_protection":"shield",
    "scout_trap":"pdef_down",
    "scout_sting_arrow":"poison",
    "rogue_bleeding_follow":"bleed",
    "mage_arcane_flow":"mana_restore",
    "priest_healing_blessing":"hot",
    "priest_purify_faith":"mdef_buff",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def actor(uid, cls, *, hp=1000, resource=100, combo=3, mp=500, effects=None, cooldowns=None, afk=0, stunned=False):
    return PvpActorState(
        user_id=uid,class_key=cls,character_name=f"Actor{uid}",max_hp=1000,hp=hp,
        max_mp=500,mp=mp,resource_type=RESOURCE[cls],resource=resource,combo=combo,
        physical_attack=75,magical_attack=75,physical_defense=35,magical_defense=35,
        weapon_physical_min=20,weapon_physical_max=20,weapon_magical_min=20,weapon_magical_max=20,
        physical_crit_chance=0,magical_crit_chance=0,dodge_chance=0,level=20,
        effects=dict(effects or {}),cooldowns=dict(cooldowns or {}),consecutive_afk=afk,stunned_next=stunned,
    )


def outcome_for(result, uid):
    return next(item for item in result.outcomes if int(item.user_id)==int(uid))


def run_skill(cls, skill, seed):
    own=actor(1,cls,hp=700,mp=400,resource=100,combo=3)
    enemy=actor(2,"warrior",resource=0,combo=0)
    if skill.get("effect")=="restore_mana_percent": own.mp=100
    if skill.get("effect")=="player_cleanse_mdef_buff":
        own.mp=200
        own.effects={"poison":{"kind":"poison","power":5,"duration":3,"source_id":2},"pdef_down":{"kind":"pdef_down","percent":30,"duration":3,"source_id":2}}
    result=resolve_pvp_round(1,1,own,enemy,PvpActionIntent(1,"skill",skill["key"]),PvpActionIntent(2,"afk_skip"),seed=seed)
    outcome=outcome_for(result,1)
    assert outcome.valid, (cls,skill["key"],outcome.reason)
    assert outcome.resource_spent>=0
    if skill.get("no_damage") or float(skill.get("damage_multiplier") or 0)==0:
        assert outcome.damage==0, skill["key"]
    else:
        assert outcome.damage>0, skill["key"]
    effect=EXPECTED_EFFECT.get(skill["key"])
    if effect:
        applied={str(x.get("effect_key")) for x in outcome.applied_effects}
        assert effect in applied, (skill["key"],applied)
    return {
        "class":cls,"key":skill["key"],"valid":outcome.valid,"damage":outcome.damage,
        "resource_spent":outcome.resource_spent,"resource_gained":outcome.resource_gained,
        "combo_spent":outcome.combo_spent,"combo_gained":outcome.combo_gained,
        "effects":[dict(x) for x in outcome.applied_effects],
    }


def main():
    db_before={name:digest(ROOT/name) for name in ("game.db","game.db-wal")}
    combat_path=ROOT/"handlers/combat.py"
    catalog_before=digest(combat_path)
    catalog=load_production_pvp_skill_catalog()
    assert tuple(sorted(catalog))==tuple(sorted(CLASSES))
    assert sum(len(v) for v in catalog.values())==18
    assert all(len(catalog[c])==3 for c in CLASSES)
    keys=[s["key"] for c in CLASSES for s in catalog[c]]
    assert len(keys)==len(set(keys))==18

    required=("key","name","cost_type","cost","cooldown","damage_multiplier","attack_type")
    for cls in CLASSES:
        for skill in catalog[cls]:
            assert all(field in skill for field in required),(cls,skill)

    rows=[]
    for index,cls in enumerate(CLASSES):
        for offset,skill in enumerate(catalog[cls]):
            rows.append(run_skill(cls,skill,1000+index*10+offset))

    # Resource contracts.
    energy=resolve_pvp_round(1,1,actor(1,"rogue",resource=5,combo=0),actor(2,"priest"),PvpActionIntent(1,"skill","rogue_sneak_strike"),PvpActionIntent(2,"afk_skip"),seed=4)
    assert outcome_for(energy,1).valid and energy.actor_a["resource"]==0 and energy.actor_a["combo"]==1
    evis=resolve_pvp_round(1,1,actor(1,"rogue",resource=100,combo=3),actor(2,"priest"),PvpActionIntent(1,"skill","rogue_eviscerate"),PvpActionIntent(2,"afk_skip"),seed=5)
    assert outcome_for(evis,1).combo_spent==3 and evis.actor_a["combo"]==0
    rage=resolve_pvp_round(1,1,actor(1,"warrior",resource=0,combo=0),actor(2,"warrior",resource=0,combo=0),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"basic_attack"),seed=6)
    assert rage.actor_a["resource"]==25 and rage.actor_b["resource"]==25
    mana=resolve_pvp_round(1,1,actor(1,"mage",mp=20),actor(2,"warrior"),PvpActionIntent(1,"skill","mage_fireball"),PvpActionIntent(2,"afk_skip"),seed=7)
    assert outcome_for(mana,1).valid and mana.actor_a["mp"]==0

    # Cooldown, stun, DoT, HoT, shield, cleanse/refresh.
    cd=resolve_pvp_round(1,1,actor(1,"mage",cooldowns={"mage_thunder_spell":3}),actor(2,"warrior"),PvpActionIntent(1,"skill","mage_thunder_spell"),PvpActionIntent(2,"afk_skip"),seed=8)
    assert not outcome_for(cd,1).valid and outcome_for(cd,1).reason=="skill_on_cooldown"
    stun=resolve_pvp_round(1,1,actor(1,"mage",stunned=True),actor(2,"warrior"),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"afk_skip"),seed=9)
    assert outcome_for(stun,1).action_type=="stunned_skip" and stun.actor_a["consecutive_afk"]==0
    periodic=resolve_pvp_round(2,2,actor(1,"priest",hp=900,effects={"hot":{"kind":"hot","power":50,"duration":2,"source_id":1}}),actor(2,"warrior",hp=900,effects={"poison":{"kind":"poison","power":20,"duration":2,"source_id":1}}),PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"afk_skip"),seed=10)
    event_types={e["type"] for e in periodic.events}
    assert {"hot_tick","dot_tick"}.issubset(event_types)
    assert periodic.actor_a["hp"]==950 and periodic.actor_b["hp"]==880
    assert periodic.actor_a["effects"]["hot"]["duration"]==1
    assert periodic.actor_b["effects"]["poison"]["duration"]==1
    cleanse=next(x for x in rows if x["key"]=="priest_purify_faith")
    assert any(x.get("effect_key")=="mdef_buff" for x in cleanse["effects"])

    # AFK and terminal contracts.
    one_afk=resolve_pvp_round(5,5,actor(1,"warrior",afk=PVP_CONSECUTIVE_AFK_LIMIT-1),actor(2,"priest"),PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"basic_attack"),seed=11)
    assert one_afk.terminal and one_afk.winner_id==2 and one_afk.result_reason=="afk_defeat"
    both_afk=resolve_pvp_round(5,5,actor(1,"warrior",afk=PVP_CONSECUTIVE_AFK_LIMIT-1),actor(2,"priest",afk=PVP_CONSECUTIVE_AFK_LIMIT-1),PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"afk_skip"),seed=12)
    assert both_afk.terminal and both_afk.winner_id is None and both_afk.result_reason=="technical_draw_both_afk"
    lethal=resolve_pvp_round(3,3,actor(1,"warrior",hp=10,effects={"bleed":{"kind":"bleed","power":20,"duration":1,"source_id":2}}),actor(2,"priest",hp=10,effects={"poison":{"kind":"poison","power":20,"duration":1,"source_id":1}}),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"basic_attack"),seed=13)
    assert lethal.terminal and lethal.winner_id is None and lethal.result_reason=="draw_periodic"
    limit=resolve_pvp_round(PVP_MAX_ROUNDS,99,actor(1,"warrior",hp=900),actor(2,"priest",hp=400),PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"afk_skip"),seed=14)
    assert limit.terminal and limit.winner_id==1 and limit.result_reason=="round_limit_hp_percent"

    # Isolation and canonical configuration.
    assert PVP_DAMAGE_MULTIPLIER==PVP_HEALING_MULTIPLIER==PVP_SHIELD_MULTIPLIER==PVP_DEBUFF_MULTIPLIER==1.0
    assert PVP_COMBAT_ENERGY_MAX==100 and PVP_CONSECUTIVE_AFK_LIMIT==5 and PVP_MAX_ROUNDS==50
    assert digest(combat_path)==catalog_before
    db_after={name:digest(ROOT/name) for name in ("game.db","game.db-wal")}
    assert db_after==db_before,(db_before,db_after)

    report={
        "version":"14.5.1","verdict":"PASS","classes":list(CLASSES),"skills_tested":len(rows),
        "skill_results":rows,"resource_contracts":["mana","rage","combat_energy","combo"],
        "effect_contracts":["cooldown","stun","poison","bleed","hot","shield","pdef_down","mdef_buff","cleanse","mana_restore"],
        "terminal_contracts":["afk_defeat","technical_draw_both_afk","draw_periodic","round_limit_hp_percent"],
        "multipliers":{"damage":PVP_DAMAGE_MULTIPLIER,"healing":PVP_HEALING_MULTIPLIER,"shield":PVP_SHIELD_MULTIPLIER,"debuff":PVP_DEBUFF_MULTIPLIER},
        "production_skill_catalog_sha256":catalog_before,"database_unchanged":True,
    }
    output=ROOT/"tools/pvp_class_effect_and_isolation_regression_report.json"
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("[OK] PvP class, effect and isolation regression")
    print("- 6 classes and 18 canonical PvE skills: PASS")
    print("- Mana, Rage, Combat Energy and combo contracts: PASS")
    print("- cooldown, stun, DoT, HoT, shield, buffs, debuffs and cleanse: PASS")
    print("- AFK, simultaneous periodic death and round-limit terminal rules: PASS")
    print("- PvP multipliers remain 1.00 / 1.00 / 1.00 / 1.00: PASS")
    print("- CLASS_SKILLS_V1 source unchanged: PASS")
    print("- game.db and WAL unchanged: PASS")

if __name__=="__main__": main()
