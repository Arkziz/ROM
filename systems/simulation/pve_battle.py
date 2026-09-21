from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from .battle_models import BattleAction, BattleActor, BattleResult
from .canonical_rules import call_rule
from .rng import SimulationRng
from .skill_catalog import load_production_skill_catalog

RESOURCE_BY_CLASS={"warrior":"rage","knight":"rage","scout":"combat_energy","rogue":"combat_energy_combo","mage":"mana","priest":"mana"}
MAGIC_CLASSES={"mage","priest"}

class ExactPveBattleEngine:
    def __init__(self, project_root: Path, seed: int, max_turns: int=100):
        self.root=Path(project_root); self.rng=SimulationRng(seed); self.seed=int(seed); self.max_turns=max_turns
        self.skills=load_production_skill_catalog(self.root)

    def _effective_def(self, actor: BattleActor, kind: str) -> int:
        value=float(actor.mdef if kind=="magical" else actor.pdef)
        key="mdef_percent" if kind=="magical" else "pdef_percent"
        for effect in actor.effects.values(): value *= 1+float(effect.get(key,0))/100
        return max(0,int(round(value)))

    def _tick_start(self, actor: BattleActor, actions: List[BattleAction], turn: int):
        for key in list(actor.cooldowns): actor.cooldowns[key]=max(0,actor.cooldowns[key]-1)
        if actor.resource_type in {"combat_energy","combat_energy_combo"}: actor.resource=min(actor.max_resource,actor.resource+20)
        for key in list(actor.effects):
            e=actor.effects[key]
            if e.get("type")=="dot" and actor.alive:
                dmg=min(actor.hp,int(e.get("damage",0))); actor.hp-=dmg
                actions.append(BattleAction(turn,"effect",key,damage=dmg,details={"target":actor.name}))
            elif e.get("type")=="hot" and actor.alive:
                heal=min(actor.max_hp-actor.hp,int(e.get("heal",0))); actor.hp+=heal
                actions.append(BattleAction(turn,"effect",key,healing=heal,details={"target":actor.name}))
            e["turns"]=int(e.get("turns",0))-1
            if e["turns"]<=0: del actor.effects[key]

    def _absorb(self, player: BattleActor, damage: int) -> int:
        for key,e in list(player.effects.items()):
            if e.get("type")=="shield" and damage>0:
                used=min(damage,int(e.get("absorb_left",0))); damage-=used; e["absorb_left"]-=used
                if e["absorb_left"]<=0: del player.effects[key]
        return damage

    def _can_use(self, actor: BattleActor, skill: Dict[str,Any]) -> bool:
        if actor.cooldowns.get(skill["key"],0)>0: return False
        typ=skill["cost_type"]; cost=int(skill.get("cost",0))
        if typ=="rage_all_min": return actor.resource>=int(skill.get("min_cost",30))
        if typ=="combat_energy_combo": return actor.resource>=cost and actor.combo>=int(skill.get("min_combo",1))
        return actor.resource>=cost

    def _choose(self, class_key: str, player: BattleActor, mob: BattleActor) -> Optional[Dict[str,Any]]:
        available=[s for s in self.skills[class_key] if self._can_use(player,s)]
        if not available: return None
        if class_key=="priest" and player.hp/player.max_hp<0.55:
            x=next((s for s in available if s.get("effect")=="player_hot" and "priest_hot" not in player.effects),None)
            if x:return x
        if class_key=="mage" and player.max_resource and player.resource/player.max_resource<0.25:
            x=next((s for s in available if s.get("effect")=="restore_mana_percent"),None)
            if x:return x
        if class_key=="knight" and player.hp/player.max_hp<0.60:
            x=next((s for s in available if s.get("effect")=="player_shield" and "knight_shield" not in player.effects),None)
            if x:return x
        if class_key=="warrior":
            finisher=next((s for s in available if s.get("scales_with_spent_rage")),None)
            if finisher:return finisher
            suppression=next((s for s in available if s.get("effect")=="enemy_pdef_down" and "warrior_pdef" not in mob.effects),None)
            if suppression:return suppression
        if class_key=="scout":
            trap=next((s for s in available if s.get("effect")=="enemy_pdef_trap" and "scout_pdef" not in mob.effects),None)
            if trap:return trap
            poison=next((s for s in available if s.get("effect")=="enemy_poison" and "enemy_poison" not in mob.effects and mob.hp>max(1,int(round(mob.max_hp*.35)))),None)
            if poison:return poison
        if class_key=="rogue" and player.combo>=3:
            x=next((s for s in available if s.get("scales_with_combo")),None)
            if x:return x
        damaging=[s for s in available if not s.get("no_damage")]
        return max(damaging,key=lambda s:float(s.get("damage_multiplier",0))) if damaging else available[0]

    def _pay(self, actor: BattleActor, skill: Dict[str,Any]) -> Dict[str,int]:
        typ=skill["cost_type"]; cost=int(skill.get("cost",0)); spent={"rage":0,"combo":0}
        if typ=="rage_all_min": spent["rage"]=actor.resource; actor.resource=0
        else: actor.resource=max(0,actor.resource-cost)
        if typ=="combat_energy_combo": spent["combo"]=actor.combo; actor.combo=0
        return spent

    def _apply_effect(self, player: BattleActor, mob: BattleActor, skill: Dict[str,Any], damage: int):
        effect=skill.get("effect")
        if effect=="enemy_pdef_down": mob.effects["warrior_pdef"]={"turns":3,"pdef_percent":-30}
        elif effect=="enemy_pdef_trap": mob.effects["scout_pdef"]={"turns":2,"pdef_percent":-50}
        elif effect in {"enemy_bleed","enemy_poison"}: mob.effects[effect]={"type":"dot","turns":3,"damage":max(2,int(round(max(1,damage)*.30)))}
        elif effect=="player_shield": player.effects["knight_shield"]={"type":"shield","turns":3,"absorb_left":max(15,int(player.pdef*2+player.level*3))}
        elif effect=="player_hot": player.effects["priest_hot"]={"type":"hot","turns":4,"heal":max(5,int(round(player.max_hp*.10)))}
        elif effect=="restore_mana_percent": player.resource=min(player.max_resource,player.resource+max(1,int(round(player.max_resource*.25))))
        elif effect=="player_cleanse_mdef_buff":
            player.effects={k:v for k,v in player.effects.items() if not v.get("negative")}; player.effects["priest_mdef"]={"turns":3,"mdef_percent":30}
            player.resource=min(player.max_resource,player.resource+max(1,int(round(player.max_resource*.15))))

    def _player_action(self, turn, class_key, p, m, actions):
        skill=self._choose(class_key,p,m)
        if skill:
            spent=self._pay(p,skill); mult=float(skill.get("damage_multiplier",0)); damage=0; crit=False
            if mult>0:
                attack=p.magic_attack if skill["attack_type"]=="magical" else p.attack
                base=call_rule("player_attack",attack,self._effective_def(m,skill["attack_type"]),p.dex,p.wis,p.level,skill["attack_type"],p.weapon_min_damage,p.weapon_max_damage,rng=self.rng)
                damage=max(1,int(round(int(base["damage"])*mult))); crit=bool(base["is_crit"])
                if skill.get("scales_with_spent_rage"): damage=max(1,int(round(damage*(1+spent["rage"]/100))))
                if skill.get("scales_with_combo"): damage=max(1,int(round(damage*(1+spent["combo"]*.50))))
                if skill.get("scales_with_player_pdef"): damage+=max(1,int(round(p.pdef*.50)))
                m.hp=max(0,m.hp-damage)
            if int(skill.get("stun_chance",0)) and self.rng.randint(1,100)<=int(skill["stun_chance"]): m.effects["stunned"]={"turns":1,"stun":True}
            if int(skill.get("combo_gain",0)): p.combo=min(p.max_combo,p.combo+int(skill["combo_gain"]))
            if int(skill.get("extra_rage",0)): p.resource=min(p.max_resource,p.resource+int(skill["extra_rage"]))
            p.cooldowns[skill["key"]]=int(skill.get("cooldown",0)); self._apply_effect(p,m,skill,damage)
            actions.append(BattleAction(turn,"player",skill["key"],damage=damage,critical=crit,details={"resource":p.resource,"combo":p.combo})); return
        kind="magical" if class_key in MAGIC_CLASSES else "physical"; attack=p.magic_attack if kind=="magical" else p.attack
        raw=call_rule("player_attack",attack,self._effective_def(m,kind),p.dex,p.wis,p.level,kind,p.weapon_min_damage,p.weapon_max_damage,rng=self.rng)
        damage=int(raw["damage"]); m.hp=max(0,m.hp-damage)
        if p.resource_type=="rage": p.resource=min(p.max_resource,p.resource+15)
        actions.append(BattleAction(turn,"player","basic_attack",damage=damage,critical=bool(raw["is_crit"])))

    def _mob_action(self, turn,p,m,actions):
        stunned=m.effects.pop("stunned",None)
        if stunned: actions.append(BattleAction(turn,"mob","stunned")); return
        raw=call_rule("mob_attack",m.attack,self._effective_def(p,"physical"),self._effective_def(p,"magical"),p.dex,m.dex,p.sta,p.level,m.attack_type,rng=self.rng)
        damage=self._absorb(p,int(raw["damage"])); p.hp=max(0,p.hp-damage)
        if p.resource_type=="rage" and damage>0:p.resource=min(p.max_resource,p.resource+10)
        actions.append(BattleAction(turn,"mob","attack",damage=damage,dodged=bool(raw["is_dodge"])))

    def run(self,battle_id,class_key,player,mob,battle_type="normal"):
        p=deepcopy(player);m=deepcopy(mob); actions=[]; p.resource_type=RESOURCE_BY_CLASS[class_key]
        if p.max_resource<=0: p.max_resource=100
        if p.resource_type=="rage": p.resource=0
        elif p.resource<=0:p.resource=p.max_resource
        for turn in range(1,self.max_turns+1):
            self._tick_start(p,actions,turn); self._tick_start(m,actions,turn)
            if not p.alive or not m.alive: break
            self._player_action(turn,class_key,p,m,actions)
            if not m.alive: break
            self._mob_action(turn,p,m,actions)
            if not p.alive: break
        turns=max((a.turn for a in actions),default=0); winner="player" if p.alive and not m.alive else "mob" if m.alive and not p.alive else "draw"
        metrics={"actions":len(actions),"player_damage":sum(a.damage for a in actions if a.actor in {"player","effect"}),"mob_damage":sum(a.damage for a in actions if a.actor=="mob"),"crits":sum(a.critical for a in actions),"dodges":sum(a.dodged for a in actions),"skills_used":sum(a.actor=="player" and a.action!="basic_attack" for a in actions),"player_resource":p.resource,"player_max_resource":p.max_resource}
        return BattleResult(battle_id,self.seed,battle_type,class_key,winner,turns,p.hp,p.max_hp,m.hp,m.max_hp,actions,metrics,"death" if winner!="draw" else "turn_limit")
