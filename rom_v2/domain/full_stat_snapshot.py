"""Canonical source-separated full player-stat snapshot for ROM V2.

This module composes the audited primary-stat and derived-stat engines. Equipment,
rune, and enhancement data arrive as already-resolved inputs; this owner does not
redefine item generation, rune levels, or refinement formulas.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

from rom_v2.domain.derived_stats import (
    DerivedStats,
    MANA_CLASSES,
    calculate_dodge,
    calculate_magical_crit,
    calculate_matk,
    calculate_max_hp,
    calculate_max_mp,
    calculate_mdef,
    calculate_patk,
    calculate_pdef,
    calculate_physical_crit,
)
from rom_v2.domain.primary_stats import PRIMARY_KEYS, PrimaryStats, base_primary_value


def _sum_primary(layers: Iterable[PrimaryStats]) -> PrimaryStats:
    """Add V1 primary-stat layers without losing their separate audit identity."""
    totals = {key: 0 for key in PRIMARY_KEYS}
    for layer in layers:
        for key in PRIMARY_KEYS:
            totals[key] += getattr(layer, key)
    return PrimaryStats(**totals)


@dataclass(frozen=True, slots=True)
class DerivedBonusLayer:
    """Precomputed flat outputs owned by equipment/refinement subsystems."""
    hp: int = 0
    mp: int = 0
    patk: int = 0
    matk: int = 0
    pdef: int = 0
    mdef: int = 0

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.values()):
            raise ValueError("derived_bonus_negative")

    def values(self) -> tuple[int, ...]:
        return (self.hp, self.mp, self.patk, self.matk, self.pdef, self.mdef)

    def add(self, other: DerivedBonusLayer) -> DerivedBonusLayer:
        return DerivedBonusLayer(*(left + right for left, right in zip(self.values(), other.values())))


@dataclass(frozen=True, slots=True)
class EquippedStatInput:
    """One equipped inventory item after its owning subsystem resolved bonuses."""
    inventory_id: str
    primary: PrimaryStats = field(default_factory=PrimaryStats)
    derived: DerivedBonusLayer = field(default_factory=DerivedBonusLayer)
    durability: int = 100
    equipped: bool = True

    def __post_init__(self) -> None:
        if not str(self.inventory_id).strip():
            raise ValueError("inventory_id_required")
        if self.durability < 0:
            raise ValueError("durability_negative")

    @property
    def contributes(self) -> bool:
        """Match V1 filtering: only equipped and non-broken items contribute."""
        return self.equipped and self.durability > 0


@dataclass(frozen=True, slots=True)
class FullStatSnapshotInput:
    """All audited source layers needed to build one player-stat snapshot."""
    class_key: str
    level: int
    allocated: PrimaryStats = field(default_factory=PrimaryStats)
    equipment: tuple[EquippedStatInput, ...] = ()
    runes: PrimaryStats = field(default_factory=PrimaryStats)
    enhancement: DerivedBonusLayer = field(default_factory=DerivedBonusLayer)
    attacker_dex: int = 0

    def __post_init__(self) -> None:
        if not str(self.class_key).strip():
            raise ValueError("class_key_required")
        if self.level < 1:
            raise ValueError("character_level_invalid")
        if self.attacker_dex < 0:
            raise ValueError("attacker_dex_negative")
        inventory_ids = [item.inventory_id for item in self.equipment]
        if len(inventory_ids) != len(set(inventory_ids)):
            raise ValueError("duplicate_equipment_inventory_id")


@dataclass(frozen=True, slots=True)
class FullStatSnapshot:
    """One immutable output shared by profile, combat, and simulator consumers."""
    class_key: str
    level: int
    base: PrimaryStats
    allocated: PrimaryStats
    equipment: PrimaryStats
    runes: PrimaryStats
    total_primary: PrimaryStats
    equipment_derived: DerivedBonusLayer
    enhancement_derived: DerivedBonusLayer
    derived: DerivedStats


def base_primary_stats(level: int) -> PrimaryStats:
    """Build the audited uniform base layer: 10 + level - 1 per primary stat."""
    value = base_primary_value(level)
    return PrimaryStats(**{key: value for key in PRIMARY_KEYS})


def build_full_stat_snapshot(source: FullStatSnapshotInput) -> FullStatSnapshot:
    """Build the sole canonical full stat snapshot from source-separated inputs."""
    base = base_primary_stats(source.level)
    active_items = tuple(item for item in source.equipment if item.contributes)
    equipment_primary = _sum_primary(item.primary for item in active_items)
    equipment_derived = DerivedBonusLayer()
    for item in active_items:
        equipment_derived = equipment_derived.add(item.derived)
    total_primary = _sum_primary((base, source.allocated, equipment_primary, source.runes))
    stat_map = {key: getattr(total_primary, key) for key in PRIMARY_KEYS}
    extra = equipment_derived.add(source.enhancement)
    class_key = source.class_key.strip().casefold()
    max_hp = calculate_max_hp(source.level, total_primary.sta) + extra.hp
    max_mp = calculate_max_mp(class_key, source.level, total_primary.int, total_primary.wis)
    if class_key in MANA_CLASSES:
        max_mp += extra.mp
    derived = DerivedStats(
        max_hp=max_hp,
        max_mp=max_mp,
        patk=calculate_patk(class_key, stat_map) + extra.patk,
        matk=calculate_matk(class_key, stat_map) + extra.matk,
        pdef=calculate_pdef(extra.pdef, total_primary.sta),
        mdef=calculate_mdef(extra.mdef, total_primary.wis),
        physical_crit=calculate_physical_crit(total_primary.dex),
        magical_crit=calculate_magical_crit(total_primary.wis),
        dodge=calculate_dodge(total_primary.dex, source.attacker_dex),
    )
    return FullStatSnapshot(
        class_key=class_key,
        level=source.level,
        base=base,
        allocated=source.allocated,
        equipment=equipment_primary,
        runes=source.runes,
        total_primary=total_primary,
        equipment_derived=equipment_derived,
        enhancement_derived=source.enhancement,
        derived=derived,
    )
