"""Pure exactly-once terminal lifecycle for ROM V2.

The module claims victory, defeat or escape through the canonical Battle
Aggregate, then returns an ordered settlement plan. It performs no persistence,
rewards, drops, penalties, domain-event delivery or presentation by itself.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from rom_v2.domain.battle import BattleAggregate,BattleEvent,BattleFailure,BattleStatus,claim_terminal
class TerminalOutcome(str,Enum):VICTORY="VICTORY";DEFEAT="DEFEAT";ESCAPE="ESCAPE"
class SettlementStep(str,Enum):
 FINALIZE_COMBAT_STATE="FINALIZE_COMBAT_STATE";VICTORY_REWARD="VICTORY_REWARD";ENEMY_DROPS="ENEMY_DROPS";DEFEAT_CONSEQUENCES="DEFEAT_CONSEQUENCES";ESCAPE_CLEANUP="ESCAPE_CLEANUP";DOWNSTREAM_EVENTS="DOWNSTREAM_EVENTS";PRESENTATION="PRESENTATION"
@dataclass(frozen=True,slots=True)
class TerminalPlan:
 outcome:TerminalOutcome;steps:tuple[SettlementStep,...]
@dataclass(frozen=True,slots=True)
class TerminalResult:
 accepted:bool;aggregate:BattleAggregate;plan:TerminalPlan|None=None;events:tuple[BattleEvent,...]=();failure:BattleFailure|None=None;duplicate:bool=False;presentation_allowed:bool=False
_STATUS={TerminalOutcome.VICTORY:BattleStatus.VICTORY,TerminalOutcome.DEFEAT:BattleStatus.DEFEAT,TerminalOutcome.ESCAPE:BattleStatus.ESCAPED}
_STEPS={
 TerminalOutcome.VICTORY:(SettlementStep.FINALIZE_COMBAT_STATE,SettlementStep.VICTORY_REWARD,SettlementStep.ENEMY_DROPS,SettlementStep.DOWNSTREAM_EVENTS,SettlementStep.PRESENTATION),
 TerminalOutcome.DEFEAT:(SettlementStep.FINALIZE_COMBAT_STATE,SettlementStep.DEFEAT_CONSEQUENCES,SettlementStep.DOWNSTREAM_EVENTS,SettlementStep.PRESENTATION),
 TerminalOutcome.ESCAPE:(SettlementStep.FINALIZE_COMBAT_STATE,SettlementStep.ESCAPE_CLEANUP,SettlementStep.DOWNSTREAM_EVENTS,SettlementStep.PRESENTATION),
}
def claim_terminal_path(aggregate:BattleAggregate,outcome:TerminalOutcome,operation_id:str)->TerminalResult:
 """Claim one absorbing terminal outcome and return one ordered plan.

 Duplicate operation IDs and already-terminal battles return no plan, no domain
 events and no presentation permission, preventing duplicate settlement/output.
 """
 if not operation_id.strip():return TerminalResult(False,aggregate,failure=BattleFailure.INVALID_RESULT)
 transition=claim_terminal(aggregate,_STATUS[outcome],operation_id)
 if transition.replayed:return TerminalResult(False,transition.aggregate,duplicate=True)
 if not transition.success:return TerminalResult(False,transition.aggregate,failure=transition.failure,duplicate=transition.failure is BattleFailure.TERMINAL_ALREADY_CLAIMED)
 plan=TerminalPlan(outcome,_STEPS[outcome])
 event=BattleEvent("BATTLE_TERMINAL_SETTLEMENT_PLANNED",aggregate.battle_id,aggregate.turn,payload={"outcome":outcome.value})
 return TerminalResult(True,transition.aggregate,plan,(*transition.events,event),presentation_allowed=True)
def can_accept_combat_action(aggregate:BattleAggregate)->bool:
 """Terminal state is absorbing; only active unclaimed battles accept actions."""
 return aggregate.status is BattleStatus.ACTIVE and not aggregate.terminal_claimed
