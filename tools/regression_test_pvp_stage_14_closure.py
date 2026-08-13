from __future__ import annotations
import inspect,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems import pvp_config as config
from systems import pvp_round_engine as engine
from systems.pvp_combat_log import render_pvp_round_combat_log
from systems.pvp_completion_service import _REASON_TEXT
from systems.pvp_models import PvpActionIntent,PvpActorState
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
CLASSES=("warrior","knight","scout","rogue","mage","priest")
PAIRS=tuple((a,b) for i,a in enumerate(CLASSES) for b in CLASSES[i+1:])
def actor(uid,cls,hp=100000):
 mana=cls in {"mage","priest"}; energy=cls in {"scout","rogue"}; rt="mana" if mana else "combat_energy_combo" if cls=="rogue" else "combat_energy" if energy else "rage"
 return PvpActorState(user_id=uid,class_key=cls,character_name=cls,max_hp=hp,hp=hp,max_mp=500 if mana else 0,mp=500 if mana else 0,resource_type=rt,resource=100,combo=0,physical_attack=50,magical_attack=50,physical_defense=100000,magical_defense=100000,weapon_physical_min=0,weapon_physical_max=0,weapon_magical_min=0,weapon_magical_max=0,physical_crit_chance=0,magical_crit_chance=0,dodge_chance=0,level=20)
assert config.PVP_MAX_ROUNDS==0 and config.PVP_CONSECUTIVE_AFK_LIMIT==5
assert config.PVP_PRODUCTION_STATE_MUTATION is False and config.PVP_POTIONS_ALLOWED is False
assert (config.PVP_DAMAGE_MULTIPLIER,config.PVP_HEALING_MULTIPLIER,config.PVP_SHIELD_MULTIPLIER,config.PVP_DEBUFF_MULTIPLIER)==(1.1375,0.8398,0.4566,0.9044)
source=inspect.getsource(engine.resolve_pvp_round)
assert "round_limit_hp_percent" not in source and "draw_round_limit_equal_hp_percent" not in source and "round_number >= PVP_MAX_ROUNDS" not in source
catalog=load_production_pvp_skill_catalog(); assert set(CLASSES)<=set(catalog); assert all(isinstance(catalog[c],tuple) and catalog[c] for c in CLASSES)
# Knight Judgement / Кара лицаря is an active production skill and was manually verified in real duels.
knight_keys={str(s.get("key") or "") for s in catalog["knight"]}; assert "knight_judgement" in knight_keys
for idx,(a,b) in enumerate(PAIRS,1):
 r=engine.resolve_pvp_round(1,idx,actor(1,a),actor(2,b),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"basic_attack"),seed=146600+idx); assert r.round_number==1
assert len(PAIRS)==15
long=engine.resolve_pvp_round(999,1000,actor(1,"warrior"),actor(2,"priest"),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"basic_attack"),seed=146699)
assert not long.terminal and long.winner_id is None and long.result_reason is None
left=actor(1,"warrior"); right=actor(2,"priest"); left.consecutive_afk=4
afk=engine.resolve_pvp_round(1000,1001,left,right,PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"basic_attack"),seed=146698)
assert afk.terminal and afk.winner_id==2 and afk.result_reason=="afk_defeat"
left=actor(1,"warrior"); right=actor(2,"priest"); left.consecutive_afk=4; right.consecutive_afk=4
both=engine.resolve_pvp_round(1001,1002,left,right,PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"afk_skip"),seed=146697)
assert both.terminal and both.winner_id is None and both.result_reason=="technical_draw_both_afk"
assert _REASON_TEXT["simultaneous"]=="перемога в бою" and _REASON_TEXT["afk_defeat"]=="5 пропущених ходів поспіль"
payload={"round_number":7,"actors":[{"user_id":1,"character_name":"A","class_key":"warrior","hp":300,"max_hp":420,"resource_type":"rage","resource":25,"mp":0,"max_mp":0},{"user_id":2,"character_name":"B","class_key":"priest","hp":320,"max_hp":426,"resource_type":"mana","resource":0,"mp":300,"max_mp":345}],"outcomes":[{"user_id":1,"action_type":"basic_attack","valid":True,"damage":36,"resource_gained":15},{"user_id":2,"action_type":"basic_attack","valid":True,"damage":48,"resource_spent":12}],"events":[{"type":"rage_gain_attack","user_id":1,"value":15,"before":0,"after":15},{"type":"rage_gain_damage_taken","user_id":1,"value":10,"before":15,"after":25}]}
text=render_pvp_round_combat_log(payload,1)
for expected in ("⚔️ <b>Раунд 7</b>","🗡 Завдано <b>36</b> шкоди.","🔥 Лють: +15 → 15/100","🔥 <b>A</b>: +10 Люті від отриманої шкоди → 25/100","❤️ A: 300/420 | B: 320/426","🔷 B: 300/345 Мана"): assert expected in text,(expected,text)
for forbidden in ("Результат раунду","раунд(и)","Витрачено ресурсу","Отримано ресурсу","Атаку було ухилено"): assert forbidden not in text
summary={"version":"14.6.6","classes":list(CLASSES),"unique_matchups_checked":15,"knight_judgement_present":True,"round_limit_disabled":True,"round_999_continues":True,"five_afk_defeat":True,"both_afk_draw":True,"localized_terminal_reasons":True,"compact_resource_grouping":True,"production_state_mutation":False}
print(json.dumps(summary,ensure_ascii=False,sort_keys=True)); print("[OK] Stage 14 PvP closure regression")
