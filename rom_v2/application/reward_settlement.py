"""Atomic exact-once reward settlement application service.

This module defines application DTOs and ports only. It does not provide a
SQLite adapter, runtime wiring, Telegram presentation, or gameplay formulas.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Any, Literal, Mapping, Protocol, Sequence

from rom_v2.domain.level_up_gold import calculate_v2_level_up_rewards
from rom_v2.domain.player_progression import PlayerProgressionResult, apply_player_exp_award

RewardSettlementSource = Literal["pve", "pve_boss"]
RewardLootStatus = Literal["applied", "pending", "rejected"]

class RewardSettlementError(RuntimeError):
    """Base application-service failure."""

class RewardSettlementInProgressError(RewardSettlementError):
    """Raised when the stable operation key is already being processed."""

class RewardSettlementValidationError(RewardSettlementError):
    """Raised before any mutation when command data is invalid."""

@dataclass(frozen=True, slots=True)
class RewardLootCommand:
    item_key: str
    quantity: int

@dataclass(frozen=True, slots=True)
class RewardObjectiveProgressCommand:
    progress_key: str
    amount: int

@dataclass(frozen=True, slots=True)
class RewardSettlementCommand:
    operation_key: str
    source_type: RewardSettlementSource
    actor_id: int
    encounter_id: str
    exp_award: int
    base_combat_gold: float
    premium_combat_gold: float = 0.0
    loot_commands: tuple[RewardLootCommand, ...] = ()
    objective_progress_commands: tuple[RewardObjectiveProgressCommand, ...] = ()

@dataclass(frozen=True, slots=True)
class RewardPlayerProgressState:
    level: int
    exp: int
    level_cap: int | None

@dataclass(frozen=True, slots=True)
class RewardLootOutcome:
    status: RewardLootStatus
    applied: tuple[RewardLootCommand, ...] = ()
    pending: tuple[RewardLootCommand, ...] = ()
    rejected: tuple[RewardLootCommand, ...] = ()

@dataclass(frozen=True, slots=True)
class RewardSettlementResult:
    operation_key: str
    status: Literal["completed"]
    duplicate: bool
    progression: PlayerProgressionResult
    level_up_rewards: Mapping[str, Any]
    combat_gold: float
    loot_outcome: RewardLootOutcome
    objective_progress: tuple[RewardObjectiveProgressCommand, ...]
    history_record_id: str

class RewardSettlementClaimRepository(Protocol):
    def claim(self, operation_key: str) -> Literal["claimed", "completed", "processing"]: ...
    def completed_result(self, operation_key: str) -> RewardSettlementResult: ...
    def complete(self, operation_key: str, result: RewardSettlementResult) -> None: ...

class RewardPlayerProgressionRepository(Protocol):
    def get_state(self, actor_id: int) -> RewardPlayerProgressState: ...
    def apply(self, actor_id: int, result: PlayerProgressionResult) -> None: ...

class RewardWalletRepository(Protocol):
    def credit(self, actor_id: int, amount: float, source: str) -> None: ...

class RewardLootRepository(Protocol):
    def apply(self, actor_id: int, commands: Sequence[RewardLootCommand]) -> RewardLootOutcome: ...

class RewardObjectiveProgressRepository(Protocol):
    def apply(self, actor_id: int, commands: Sequence[RewardObjectiveProgressCommand]) -> tuple[RewardObjectiveProgressCommand, ...]: ...

class RewardHistoryRepository(Protocol):
    def append(self, operation_key: str, actor_id: int, summary: Mapping[str, Any]) -> str: ...

class RewardSettlementUnitOfWork(Protocol):
    claims: RewardSettlementClaimRepository
    progression: RewardPlayerProgressionRepository
    wallet: RewardWalletRepository
    loot: RewardLootRepository
    objective_progress: RewardObjectiveProgressRepository
    history: RewardHistoryRepository
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class RewardSettlementService:
    """Orchestrate one exact-once PvE settlement through one Unit of Work."""
    def settle(self, command: RewardSettlementCommand, uow: RewardSettlementUnitOfWork) -> RewardSettlementResult:
        self._validate(command)
        try:
            claim = uow.claims.claim(command.operation_key)
            if claim == "completed":
                previous = uow.claims.completed_result(command.operation_key)
                return replace(previous, duplicate=True)
            if claim == "processing":
                raise RewardSettlementInProgressError(command.operation_key)
            if claim != "claimed":
                raise RewardSettlementError(f"unsupported_claim_outcome:{claim}")

            initial = uow.progression.get_state(command.actor_id)
            progression = apply_player_exp_award(
                initial.level, initial.exp, command.exp_award, initial.level_cap
            )
            level_rewards = calculate_v2_level_up_rewards(initial.level, progression.level)
            uow.progression.apply(command.actor_id, progression)

            level_gold = float(level_rewards["gold"])
            if level_gold:
                uow.wallet.credit(command.actor_id, level_gold, "level_up_gold")
            combat_gold = float(command.base_combat_gold) + float(command.premium_combat_gold)
            if combat_gold:
                uow.wallet.credit(command.actor_id, combat_gold, "combat_gold")

            loot_outcome = uow.loot.apply(command.actor_id, command.loot_commands)
            if loot_outcome.status not in ("applied", "pending", "rejected"):
                raise RewardSettlementError(f"unsupported_loot_outcome:{loot_outcome.status}")
            objective_progress = uow.objective_progress.apply(
                command.actor_id, command.objective_progress_commands
            )
            summary = {
                "source_type": command.source_type,
                "encounter_id": command.encounter_id,
                "exp_award": command.exp_award,
                "level_ups": progression.level_ups,
                "level_up_gold": level_gold,
                "combat_gold": combat_gold,
                "loot_status": loot_outcome.status,
                "objective_progress_count": len(objective_progress),
            }
            history_record_id = uow.history.append(
                command.operation_key, command.actor_id, summary
            )
            result = RewardSettlementResult(
                operation_key=command.operation_key,
                status="completed",
                duplicate=False,
                progression=progression,
                level_up_rewards=level_rewards,
                combat_gold=combat_gold,
                loot_outcome=loot_outcome,
                objective_progress=objective_progress,
                history_record_id=history_record_id,
            )
            uow.claims.complete(command.operation_key, result)
            uow.commit()
            return result
        except Exception:
            uow.rollback()
            raise

    @staticmethod
    def _validate(command: RewardSettlementCommand) -> None:
        if not command.operation_key.strip():
            raise RewardSettlementValidationError("operation_key_required")
        if command.source_type not in ("pve", "pve_boss"):
            raise RewardSettlementValidationError("unsupported_source_type")
        if int(command.actor_id) <= 0:
            raise RewardSettlementValidationError("positive_actor_id_required")
        if not command.encounter_id.strip():
            raise RewardSettlementValidationError("encounter_id_required")
        if int(command.exp_award) < 0:
            raise RewardSettlementValidationError("negative_exp_award_forbidden")
        if float(command.base_combat_gold) < 0 or float(command.premium_combat_gold) < 0:
            raise RewardSettlementValidationError("negative_combat_gold_forbidden")
        if any(not item.item_key.strip() or int(item.quantity) <= 0 for item in command.loot_commands):
            raise RewardSettlementValidationError("invalid_loot_command")
        if any(not item.progress_key.strip() or int(item.amount) <= 0 for item in command.objective_progress_commands):
            raise RewardSettlementValidationError("invalid_objective_progress_command")
