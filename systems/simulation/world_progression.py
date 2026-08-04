from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from .behavior_policy import BehaviorPolicy
from .models import SimulationEquipment, SimulationInventory
from .progression_models import PROFILES, ProgressionEvent, ProgressionResult
from .progression_provider import ProgressionProvider
from .pve_battle import ExactPveBattleEngine
from .rng import SimulationRng
from .survival_state import PersistentCombatState, SimulationSurvivalService
from .loot_equipment_city import SimulationLootEquipmentCityService
from .meta_progression import SimulationMetaProgressionService


class WorldProgressionSimulator:
    def __init__(self, project_root: Path, character_class: str, target_level: int, profile: str, seed: int, inventory_capacity: int = 40, max_days: int = 365, provider: Optional[ProgressionProvider] = None):
        if profile not in PROFILES:
            raise ValueError(f"unsupported profile: {profile}")
        if character_class not in {"warrior", "knight", "scout", "rogue", "mage", "priest"}:
            raise ValueError(f"unsupported class: {character_class}")
        if target_level < 2:
            raise ValueError("target_level must be at least 2")
        self.root = Path(project_root)
        self.character_class = character_class
        self.target_level = int(target_level)
        self.profile = PROFILES[profile]
        self.seed = int(seed)
        self.max_days = int(max_days)
        self.provider = provider or ProgressionProvider()
        self.rng = SimulationRng(seed)
        self.policy = BehaviorPolicy()
        self.inventory = SimulationInventory(capacity=inventory_capacity, reserve_slots=2)
        self.equipment = SimulationEquipment()
        self.provider.bind_state(self.inventory, self.equipment)

    def run(self) -> ProgressionResult:
        level = 1
        exp = 0
        gold = 0.0
        energy = 40
        battles = wins = deaths = 0
        energy_spent = energy_regenerated = 0
        exp_gained = 0
        gold_gained = 0.0
        city_visits = full_bag_events = items_awarded = items_lost = 0
        elapsed = 0
        events = []
        initial_actor = self.provider.player_actor(self.character_class, 1)
        survival = PersistentCombatState(initial_actor.max_hp, initial_actor.max_hp, initial_actor.max_resource, initial_actor.max_resource)
        survival_service = SimulationSurvivalService(self.inventory, self.equipment)
        loot_city = SimulationLootEquipmentCityService(self.character_class, self.inventory, self.equipment, self.rng)
        meta = SimulationMetaProgressionService(self.inventory, self.equipment, self.rng)
        run_id = f"progress_{self.character_class}_l{self.target_level}_{self.profile.key}_{self.seed}"

        for day in range(1, self.max_days + 1):
            meta.start_day(day)
            # Offline interval always restores the capped 40 energy before the next daily window.
            regenerated = max(0, 40 - energy)
            energy = 40
            energy_regenerated += regenerated
            start = (day - 1) * 1440 + self.profile.start_hour * 60
            end = (day - 1) * 1440 + self.profile.end_hour * 60
            elapsed = max(elapsed, start)

            while elapsed < end and level < self.target_level:
                if energy <= 0:
                    elapsed += 5
                    if elapsed < end:
                        energy = min(40, energy + 1)
                        energy_regenerated += 1
                        healed = survival.passive_hp_regen(5)
                        if healed: events.append(ProgressionEvent(elapsed, day, "hp_regen", {"amount": healed, "hp": survival.hp}))
                    continue

                available = self.provider.mobs(level)
                contract = meta.ensure_contract(level, available)
                selected = self.policy.select_mob(level, available, contract.target_name if contract else None)
                if selected is None:
                    raise RuntimeError(f"production content gap: no mob for player level {level}; current max mob level={self.provider.content_max_mob_level()}")

                battle_seed = self.rng.randint(1, 2_147_483_647)
                result = ExactPveBattleEngine(self.root, battle_seed).run(
                    f"{run_id}_b{battles + 1}", self.character_class,
                    self.provider.player_actor(self.character_class, level, survival.hp, survival.mp),
                    self.provider.mob_actor(selected), "normal",
                )
                battles += 1
                energy -= 1
                energy_spent += 1
                elapsed += max(1, result.turns)

                survival.hp = result.player_hp
                survival.mp = int(result.metrics.get("player_resource", survival.mp))
                survival.restore_mp_after_combat()

                if result.winner == "player":
                    wins += 1
                    gained_exp, gained_gold = self.provider.reward(level, selected, self.rng)
                    exp += gained_exp
                    exp_gained += gained_exp
                    gold += gained_gold
                    gold_gained += gained_gold
                    meta.on_victory(selected, level)
                    contract_exp = meta.claim_contract()
                    if contract_exp:
                        exp += contract_exp
                        exp_gained += contract_exp
                        events.append(ProgressionEvent(elapsed, day, "contract_claim", {"exp": contract_exp, "contracts": meta.state.contracts_completed_today}))
                    if meta.claim_daily():
                        items_awarded += 13
                        events.append(ProgressionEvent(elapsed, day, "daily_claim", {"potions": 3, "firius_tokens": 10}))
                    loot = loot_city.process_victory(selected)
                    items_awarded += loot.awarded
                    items_lost += loot.lost
                    full_bag_events += loot.full_bag_events
                    events.append(ProgressionEvent(elapsed, day, "victory", {"level": level, "mob": selected["name"], "exp": gained_exp, "gold": gained_gold, "loot_awarded": loot.awarded, "loot_lost": loot.lost, "equipment": loot.equipment}))
                    transition = self.provider.apply_exp(level, exp - gained_exp, gained_exp)
                    old_level = level
                    level = transition["level"]
                    exp = transition["exp"]
                    for reached_level in range(old_level + 1, level + 1):
                        events.append(ProgressionEvent(elapsed, day, "level_up", {"level": reached_level}))
                else:
                    deaths += 1
                    durability = survival_service.damage_on_death()
                    survival.apply_death()
                    events.append(ProgressionEvent(elapsed, day, "death", {"level": level, "mob": selected["name"], "hp": 1, "durability_items": durability.changed, "broken": durability.broken}))
                    elapsed += 10
                    healed = survival.passive_hp_regen(10)
                    if healed: events.append(ProgressionEvent(elapsed, day, "hp_regen", {"amount": healed, "hp": survival.hp}))

                equipped_durability = [item.durability for item in survival_service.equipped_items()]
                maintenance = self.policy.maintenance(equipped_durability, self.inventory.free_slots)
                if maintenance:
                    city_visits += 1
                    gold, repair = survival_service.urgent_repair(gold, self.policy.repair_threshold)
                    gold, city = loot_city.city_maintenance(gold)
                    fused = meta.fuse_available_runes()
                    inserted = meta.insert_best_runes()
                    refined = meta.refine_best()
                    events.append(ProgressionEvent(elapsed, day, "city_visit", {"reason": maintenance.reason, "free_slots": self.inventory.free_slots, "repaired": repair.repaired, "repair_cost": repair.cost, "repair_skipped": repair.skipped_for_gold, "equipped": city.equipped, "sold_items": city.sold_items, "sold_quantity": city.sold_quantity, "sale_gold": city.gold_received, "rune_fusions": fused, "runes_inserted": inserted, "refined": bool(refined), "guild_exp": meta.state.guild.exp}))
                    elapsed += 5
                    healed = survival.passive_hp_regen(5)
                    if healed: events.append(ProgressionEvent(elapsed, day, "hp_regen", {"amount": healed, "hp": survival.hp}))

            if level >= self.target_level:
                days = day
                break
        else:
            days = self.max_days

        status = "completed" if level >= self.target_level else "max_days_reached"
        return ProgressionResult(
            run_id, self.character_class, self.target_level, level, self.profile.key, self.seed,
            days, elapsed, battles, wins, deaths, energy_spent, energy_regenerated,
            exp_gained, gold_gained, gold, city_visits, full_bag_events, items_awarded,
            items_lost, self.inventory.free_slots, events, status,
        )
