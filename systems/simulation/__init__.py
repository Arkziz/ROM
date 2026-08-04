"""Deterministic, database-free ROM simulation foundation (Stage 13.1)."""
from .clock import SimulationClock
from .config import SimulationConfig, SimulationProfile
from .metrics import SimulationEvent, SimulationMetrics
from .models import (
    EQUIPMENT_SLOT_KEYS,
    SimulationCharacter,
    SimulationContract,
    SimulationDailyQuest,
    SimulationEquipment,
    SimulationGuildProgress,
    SimulationInventory,
    SimulationInventoryItem,
    SimulationRuneSocket,
    SimulationRunResult,
    SimulationState,
)
from .reporting import build_markdown_report, write_simulation_reports
from .rng import SimulationRng

__all__ = [
    "EQUIPMENT_SLOT_KEYS", "SimulationCharacter", "SimulationClock",
    "SimulationConfig", "SimulationContract", "SimulationDailyQuest",
    "SimulationEquipment", "SimulationEvent", "SimulationGuildProgress",
    "SimulationInventory", "SimulationInventoryItem", "SimulationMetrics",
    "SimulationProfile", "SimulationRng", "SimulationRuneSocket",
    "SimulationRunResult", "SimulationState", "build_markdown_report",
    "write_simulation_reports",
]

from .canonical_rules import CanonicalRuleDescriptor, CanonicalRuleError, call_rule, rule_manifest
from .production_parity import run_required_parity, source_dependency_report
from .rng_adapter import RandomModuleAdapter, inject_module_rng
