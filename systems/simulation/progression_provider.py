from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

from data.locations import LOCATIONS, LOCATION_ORDER
from data.mobs import get_mobs_for_location
from data.player_progression import apply_exp_award, get_exp_to_next_level
from systems.combat_system import ELITE_CHANCE_PERCENT, apply_elite_modifier, build_mob, get_available_mobs
from systems.boss_system import generate_hunt_encounter
from .battle_models import BattleActor
from .combat_actor_stats import build_battle_actor
from .models import SimulationEquipment, SimulationInventory
from .canonical_rules import call_rule
from .rng import SimulationRng

# Stage 13.6.1 keeps the existing combat actor fixture only. EXP curve, content pool,
# location availability and victory rewards now come from production sources.
@dataclass
class ProgressionProvider:
    def exp_to_next(self, level: int) -> int:
        return get_exp_to_next_level(level)

    def bind_state(self, inventory: SimulationInventory, equipment: SimulationEquipment):
        self.inventory = inventory
        self.equipment = equipment
        return self

    def apply_exp(self, level: int, exp: int, amount: int) -> dict:
        return apply_exp_award(level, exp, amount)

    def location_for_level(self, level: int) -> str:
        unlocked = [key for key in LOCATION_ORDER if int(LOCATIONS[key].get("unlock_level", 1)) <= int(level)]
        if not unlocked:
            return "start_path"
        matching = [key for key in unlocked if int(LOCATIONS[key].get("level_min", 1)) <= level <= int(LOCATIONS[key].get("level_max", 999))]
        return matching[-1] if matching else unlocked[-1]

    def mobs(self, player_level: int) -> List[Dict]:
        location_id = self.location_for_level(player_level)
        return [dict(mob) for mob in get_available_mobs(player_level, location_id)]

    def resolve_encounter(self, player_level: int, selected_template: Dict, rng: SimulationRng, *, boss_enabled: bool = True, boss_chance_percent: float | None = None) -> Dict:
        location_id = self.location_for_level(player_level)
        template = dict(selected_template)
        def normal_factory(selected_template_override=None):
            return build_mob(dict(selected_template_override or template))
        encounter = generate_hunt_encounter(
            player_level=player_level,
            location_id=location_id,
            normal_mob_factory=normal_factory,
            elite_modifier=apply_elite_modifier,
            elite_roll=lambda: rng.randint(1, 100) <= int(ELITE_CHANCE_PERCENT),
            rng=rng,
            boss_enabled=boss_enabled,
            boss_chance_percent=boss_chance_percent,
            event_enabled=False,
        )
        mob = dict(encounter["mob"])
        mob["enemy_type"] = str(encounter["enemy_type"])
        mob.setdefault("mob_type", mob["enemy_type"])
        return mob

    def reward(self, player_level: int, mob: Dict, rng: SimulationRng) -> tuple[int, float]:
        exp = int(call_rule("exp_reward", player_level, mob, rng=rng))
        gold = float(call_rule("gold_reward", player_level, mob, rng=rng))
        return exp, gold

    def content_max_mob_level(self) -> int:
        values=[]
        for location_id in LOCATION_ORDER:
            values.extend(int(mob.get("level", 1)) for mob in get_mobs_for_location(location_id))
        return max(values) if values else 0

    def player_actor(self, character_class: str, level: int, current_hp: int | None = None, current_mp: int | None = None) -> BattleActor:
        inventory = getattr(self, "inventory", SimulationInventory())
        equipment = getattr(self, "equipment", SimulationEquipment())
        return build_battle_actor(character_class, level, inventory, equipment, current_hp, current_mp)

    def mob_actor(self, data: Dict) -> BattleActor:
        return BattleActor(str(data["name"]),int(data.get("level",1)),int(data.get("hp",data.get("max_hp",1))),int(data.get("max_hp",data.get("hp",1))),int(data.get("attack",1)),int(data.get("attack",1)),int(data.get("pdef",data.get("def",0))),int(data.get("mdef",data.get("def",0))),int(data.get("dex",0)),int(data.get("wis",0)),int(data.get("sta",0)),str(data.get("attack_type","physical")))
