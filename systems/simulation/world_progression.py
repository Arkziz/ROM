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
from .loot_equipment_city import POTIONS, SimulationLootEquipmentCityService
from .meta_progression import SimulationMetaProgressionService
from .potion_affordability import HP_IDS, MP_IDS, POTION_CATALOG, PotionAffordabilityLedger, affordable_small, inventory_potions


def _encounter_type(mob: Dict) -> str:
    if bool(mob.get("is_boss")) or str(mob.get("enemy_type", "")).lower() == "boss":
        return "boss"
    if bool(mob.get("is_elite")) or str(mob.get("enemy_type", "")).lower() == "elite":
        return "elite"
    return "normal"


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
        potion_ledger = PotionAffordabilityLedger()
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

                hp_potions = inventory_potions(self.inventory.items, HP_IDS)
                mp_potions = inventory_potions(self.inventory.items, MP_IDS)
                mana_class = self.character_class in {"mage", "priest"}
                potion = self.policy.choose_potion(survival.hp, survival.max_hp, survival.mp, survival.max_mp, mana_class, hp_potions, mp_potions)
                if potion:
                    kind = "hp" if potion.action == "use_hp_potion" else "mp"
                    item_id = int(potion.payload["item_id"])
                    maximum = survival.max_hp if kind == "hp" else survival.max_mp
                    current = survival.hp if kind == "hp" else survival.mp
                    restored = min(maximum - current, int(potion.payload["restore"]))
                    if restored > 0 and meta._consume(item_id, 1):
                        if kind == "hp": survival.hp += restored
                        else: survival.mp += restored
                        potion_ledger.record_free_use(item_id)
                        events.append(ProgressionEvent(elapsed, day, "potion_used", {"source":"owned_or_dropped","kind":kind,"item_id":item_id,"restore":restored}))
                else:
                    need_hp = survival.max_hp > 0 and survival.hp / survival.max_hp < self.policy.hp_potion_threshold
                    need_mp = mana_class and survival.max_mp > 0 and survival.mp / survival.max_mp < self.policy.mp_potion_threshold
                    kind = "hp" if need_hp else "mp" if need_mp else None
                    item_id = affordable_small(kind, gold) if kind else None
                    if item_id is not None:
                        row = POTION_CATALOG[item_id]; cost = float(row["buy_price"]); gold = round(gold - cost, 2)
                        restored = min((survival.max_hp-survival.hp) if kind=="hp" else (survival.max_mp-survival.mp), int(row["restore"]))
                        if kind == "hp": survival.hp += restored
                        else: survival.mp += restored
                        potion_ledger.buy_and_use(item_id)
                        events.append(ProgressionEvent(elapsed, day, "potion_purchased_and_used", {"kind":kind,"item_id":item_id,"cost":cost,"restore":restored,"gold_after":gold}))
                if survival.max_hp > 0 and survival.hp / survival.max_hp <= 0.25:
                    elapsed += 5
                    healed = survival.passive_hp_regen(5)
                    events.append(ProgressionEvent(elapsed, day, "pre_hunt_hp_wait", {"threshold_percent": 25, "healed": healed, "hp": survival.hp, "max_hp": survival.max_hp}))
                    continue

                available = self.provider.mobs(level)
                contract = meta.ensure_contract(level, available)
                allowed = [mob for mob in available if abs(int(mob.get("level", 1)) - int(level)) <= 1 and int(mob.get("min_player_level", 1)) <= int(level)]
                contract_target = contract.target_name if contract else ""
                selected = next((mob for mob in allowed if contract_target and str(mob.get("name", "")) == contract_target), None)
                selection_reason = "contract_target" if selected is not None else "seeded_random"
                if selected is None and allowed:
                    selected = self.rng.choice(allowed)
                if selected is None:
                    raise RuntimeError(f"production content gap: no mob for player level {level}; current max mob level={self.provider.content_max_mob_level()}")
                selected_template = selected
                selected = self.provider.resolve_encounter(level, selected_template, self.rng)
                if bool(selected.get("is_boss")):
                    selection_reason = "canonical_boss_roll"
                elif bool(selected.get("is_elite")):
                    selection_reason = "canonical_elite_roll"

                battle_seed = self.rng.randint(1, 2_147_483_647)
                result = ExactPveBattleEngine(self.root, battle_seed).run(
                    f"{run_id}_b{battles + 1}", self.character_class,
                    self.provider.player_actor(self.character_class, level, survival.hp, survival.mp),
                    self.provider.mob_actor(selected), _encounter_type(selected),
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
                        items_awarded += 8
                        events.append(ProgressionEvent(elapsed, day, "daily_claim", {"potions": 3, "firius_tokens": 5}))
                    loot = loot_city.process_victory(selected)
                    items_awarded += loot.awarded
                    items_lost += loot.lost
                    full_bag_events += loot.full_bag_events
                    gold, equipment_resolution = loot_city.resolve_equipment_after_victory(gold)
                    events.append(ProgressionEvent(elapsed, day, "victory", {"level": level, "player_level": level, "mob": selected["name"], "mob_level": int(selected.get("level", level)), "level_delta": int(selected.get("level", level)) - int(level), "location_id": str(selected.get("location_id", self.provider.location_for_level(level))), "attack_type": str(selected.get("attack_type", "physical")), "trash_items": list(selected.get("trash_items", []) or []), "selection_reason": selection_reason, "candidate_count": len(allowed), "encounter_type": _encounter_type(selected), "battle_outcome": "victory", "battle_turns": result.turns, "exp": gained_exp, "gold": gained_gold, "loot_awarded": loot.awarded, "loot_lost": loot.lost, "equipment": loot.equipment, "loot_records": loot.records}))
                    if equipment_resolution["equipped"] or equipment_resolution["sale_records"]:
                        events.append(ProgressionEvent(elapsed, day, "equipment_resolution", equipment_resolution))
                    inserted = meta.insert_best_runes(self.character_class)
                    refined = meta.refine_best()
                    if inserted or refined or meta.state.refine_attempts:
                        events.append(ProgressionEvent(elapsed, day, "resource_maintenance", {"runes_inserted": inserted, "refined": bool(refined), "refine_attempts_total": meta.state.refine_attempts, "refine_successes_total": meta.state.refine_successes}))
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
                    events.append(ProgressionEvent(elapsed, day, "death", {"level": level, "player_level": level, "mob": selected["name"], "mob_level": int(selected.get("level", level)), "level_delta": int(selected.get("level", level)) - int(level), "location_id": str(selected.get("location_id", self.provider.location_for_level(level))), "attack_type": str(selected.get("attack_type", "physical")), "trash_items": list(selected.get("trash_items", []) or []), "selection_reason": selection_reason, "candidate_count": len(allowed), "encounter_type": _encounter_type(selected), "battle_outcome": "defeat", "battle_turns": result.turns, "hp": 1, "durability_items": durability.changed, "broken": durability.broken}))
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
                    inserted = meta.insert_best_runes(self.character_class)
                    refined = meta.refine_best()
                    events.append(ProgressionEvent(elapsed, day, "city_visit", {"reason": maintenance.reason, "free_slots": self.inventory.free_slots, "repaired": repair.repaired, "repair_cost": repair.cost, "repair_skipped": repair.skipped_for_gold, "equipped": city.equipped, "sold_items": city.sold_items, "sold_quantity": city.sold_quantity, "sale_gold": city.gold_received, "sale_records": city.records, "rune_fusions": fused, "runes_inserted": inserted, "refined": bool(refined), "guild_exp": meta.state.guild.exp}))
                    elapsed += 5
                    healed = survival.passive_hp_regen(5)
                    if healed: events.append(ProgressionEvent(elapsed, day, "hp_regen", {"amount": healed, "hp": survival.hp}))

            if level >= self.target_level:
                days = day
                break
        else:
            days = self.max_days

        equipped_ids = {value for value in self.equipment.slots.values() if value}
        final_items = [{"simulation_item_id": item.simulation_item_id, "item_id": item.item_id, "name": item.name, "category": item.category, "rarity": item.rarity, "quantity": item.quantity, "slot_key": item.slot_key, "item_level": item.item_level, "armor_type": item.armor_type, "refine_level": item.refine_level, "durability": item.durability, "stats": dict(item.stats), "runes": [asdict(rune) for rune in item.runes], "destination": "equipped" if item.simulation_item_id in equipped_ids else "remaining"} for item in self.inventory.items]
        events.append(ProgressionEvent(elapsed, days, "simulation_final_state", {"gold": round(gold,2), "equipment_slots": dict(self.equipment.slots), "inventory": final_items, "guild_exp": meta.state.guild.exp, "refine_attempts": meta.state.refine_attempts, "refine_successes": meta.state.refine_successes, "potion_affordability": potion_ledger.to_dict(gold_gained)}))
        status = "completed" if level >= self.target_level else "max_days_reached"
        return ProgressionResult(
            run_id, self.character_class, self.target_level, level, self.profile.key, self.seed,
            days, elapsed, battles, wins, deaths, energy_spent, energy_regenerated,
            exp_gained, gold_gained, gold, city_visits, full_bag_events, items_awarded,
            items_lost, self.inventory.free_slots, events, status,
        )
