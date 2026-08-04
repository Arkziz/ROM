from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

EQUIPMENT_SLOT_KEYS = (
    "main_hand", "off_hand", "helmet", "shoulders", "chest",
    "gloves", "legs", "boots", "necklace", "ring",
)


@dataclass
class SimulationRuneSocket:
    slot_index: int
    rune_item_id: int
    stat: str
    level: int


@dataclass
class SimulationInventoryItem:
    simulation_item_id: int
    item_id: int
    name: str
    category: str
    quantity: int = 1
    max_stack: int = 1
    slot_key: str = ""
    item_level: int = 1
    rarity: str = "common"
    durability: int = 100
    refine_level: int = 0
    armor_type: str = ""
    item_subtype: str = ""
    weapon_hands: int = 1
    sell_price: float = 0.0
    stats: Dict[str, float] = field(default_factory=dict)
    runes: List[SimulationRuneSocket] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.simulation_item_id <= 0 or self.item_id <= 0:
            raise ValueError("item identifiers must be positive")
        if self.quantity <= 0 or self.max_stack <= 0 or self.quantity > self.max_stack:
            raise ValueError("invalid stack quantity")
        if not (0 <= self.durability <= 100):
            raise ValueError("durability must be in range 0..100")
        if self.refine_level < 0:
            raise ValueError("refine level cannot be negative")
        if self.category == "equipment" and self.quantity != 1:
            raise ValueError("generated equipment must be a single instance")

    @property
    def is_equipment(self) -> bool:
        return self.category == "equipment"

    @property
    def free_stack_space(self) -> int:
        return self.max_stack - self.quantity


@dataclass
class SimulationInventory:
    capacity: int = 40
    reserve_slots: int = 2
    items: List[SimulationInventoryItem] = field(default_factory=list)
    next_simulation_item_id: int = 1

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if not (0 <= self.reserve_slots < self.capacity):
            raise ValueError("invalid reserve slot count")
        self.validate()

    @property
    def used_slots(self) -> int:
        return len(self.items)

    @property
    def free_slots(self) -> int:
        return self.capacity - self.used_slots

    @property
    def utilization(self) -> float:
        return self.used_slots / self.capacity

    @property
    def should_visit_city(self) -> bool:
        return self.free_slots <= self.reserve_slots

    def validate(self) -> None:
        if len(self.items) > self.capacity:
            raise ValueError("inventory exceeds capacity")
        ids = [item.simulation_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate simulation item id")
        for item in self.items:
            item.__post_init__()

    def allocate_id(self) -> int:
        value = self.next_simulation_item_id
        self.next_simulation_item_id += 1
        return value


@dataclass
class SimulationEquipment:
    slots: Dict[str, Optional[int]] = field(
        default_factory=lambda: {key: None for key in EQUIPMENT_SLOT_KEYS}
    )

    def __post_init__(self) -> None:
        unknown = set(self.slots) - set(EQUIPMENT_SLOT_KEYS)
        if unknown:
            raise ValueError(f"unknown equipment slots: {sorted(unknown)}")
        for key in EQUIPMENT_SLOT_KEYS:
            self.slots.setdefault(key, None)


@dataclass
class SimulationContract:
    target_mob_name: str = ""
    target_level: int = 0
    target_kills: int = 5
    current_kills: int = 0
    status: str = "none"
    created_day: str = ""


@dataclass
class SimulationDailyQuest:
    quest_id: str = "kill_25_monsters"
    progress: int = 0
    target_count: int = 25
    completed: bool = False
    reward_claimed: bool = False
    day: str = ""


@dataclass
class SimulationGuildProgress:
    exp: int = 0
    resource: int = 0
    kills: int = 0
    contracts: int = 0


@dataclass
class SimulationCharacter:
    character_class: str
    level: int = 1
    exp: int = 0
    gold: float = 0.0
    hp: int = 100
    max_hp: int = 100
    mp: int = 0
    max_mp: int = 0
    energy: int = 40
    kills: int = 0
    location_id: str = "start_path"
    stats: Dict[str, int] = field(default_factory=lambda: {"str": 1, "dex": 1, "int": 1, "wis": 1, "sta": 1})
    class_resources: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.level < 1 or self.exp < 0 or self.gold < 0:
            raise ValueError("invalid character progression")
        if not (0 <= self.hp <= self.max_hp) or not (0 <= self.mp <= self.max_mp):
            raise ValueError("invalid HP or MP")
        if self.energy < 0:
            raise ValueError("energy cannot be negative")


@dataclass
class SimulationState:
    run_id: str
    character: SimulationCharacter
    inventory: SimulationInventory
    equipment: SimulationEquipment = field(default_factory=SimulationEquipment)
    contract: SimulationContract = field(default_factory=SimulationContract)
    daily: SimulationDailyQuest = field(default_factory=SimulationDailyQuest)
    guild: SimulationGuildProgress = field(default_factory=SimulationGuildProgress)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.character.__post_init__()
        self.inventory.validate()
        owned_ids = {item.simulation_item_id for item in self.inventory.items}
        for slot, item_id in self.equipment.slots.items():
            if item_id is not None and item_id not in owned_ids:
                raise ValueError(f"equipped item in {slot} is absent from inventory")
        main_id = self.equipment.slots.get("main_hand")
        off_id = self.equipment.slots.get("off_hand")
        if main_id and off_id:
            main = next(item for item in self.inventory.items if item.simulation_item_id == main_id)
            if int(main.weapon_hands) == 2:
                raise ValueError("two-handed main hand cannot coexist with off hand")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class SimulationRunResult:
    run_id: str
    schema_version: str
    config: Dict[str, Any]
    config_fingerprint: str
    seed: int
    rng: Dict[str, Any]
    clock_start: str
    clock_end: str
    state: Dict[str, Any]
    metrics: Dict[str, Any]
    status: str = "completed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
