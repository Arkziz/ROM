"""Pure deterministic Battle Aggregate shared by V2 combat consumers.

The aggregate owns identity, actor snapshots, mutable-in-battle resources, ordering,
action/result application and single-claim terminal state. Damage, skill, effect,
reward, persistence and presentation policies are intentionally external stages.
"""
from __future__ import annotations
from dataclasses import dataclass,replace
from enum import Enum
from typing import Mapping

class BattleMode(str,Enum):
    PVE="PVE"
    PVP="PVP"

class BattleStatus(str,Enum):
    ACTIVE="ACTIVE"
    VICTORY="VICTORY"
    DEFEAT="DEFEAT"
    ESCAPED="ESCAPED"
    COMPLETED="COMPLETED"

class BattleActionKind(str,Enum):
    ATTACK="ATTACK"
    SKILL="SKILL"
    ITEM="ITEM"
    ESCAPE="ESCAPE"
    WAIT="WAIT"

class BattleFailure(str,Enum):
    NOT_ACTIVE="NOT_ACTIVE"
    WRONG_ACTOR="WRONG_ACTOR"
    STALE_TURN="STALE_TURN"
    DUPLICATE_OPERATION="DUPLICATE_OPERATION"
    INVALID_RESULT="INVALID_RESULT"
    TERMINAL_ALREADY_CLAIMED="TERMINAL_ALREADY_CLAIMED"

@dataclass(frozen=True,slots=True)
class ActorSnapshot:
    """Immutable combat-start identity and resolved stat snapshot."""
    actor_id:str
    user_id:int|None
    max_hp:int
    max_mp:int
    stats:Mapping[str,int|float]
    actor_kind:str

    def __post_init__(self)->None:
        if not self.actor_id:raise ValueError("missing_actor_id")
        if self.max_hp<=0 or self.max_mp<0:raise ValueError("invalid_actor_limits")
        if self.user_id is not None and self.user_id<=0:raise ValueError("invalid_user_id")

@dataclass(frozen=True,slots=True)
class ActorResources:
    """Current battle resources, separate from immutable actor stats."""
    hp:int
    mp:int
    rage:int=0
    energy:int=0
    combo:int=0

    def __post_init__(self)->None:
        if min(self.hp,self.mp,self.rage,self.energy,self.combo)<0:raise ValueError("negative_resource")

@dataclass(frozen=True,slots=True)
class BattleActor:
    snapshot:ActorSnapshot
    resources:ActorResources

    def __post_init__(self)->None:
        if self.resources.hp>self.snapshot.max_hp or self.resources.mp>self.snapshot.max_mp:raise ValueError("resource_above_snapshot_limit")

@dataclass(frozen=True,slots=True)
class BattleAction:
    """Stable technical command; presentation text is never identity."""
    operation_id:str
    actor_id:str
    kind:BattleActionKind
    expected_turn:int
    skill_id:str|None=None
    item_inventory_id:int|None=None

    def __post_init__(self)->None:
        if not self.operation_id or not self.actor_id:raise ValueError("missing_action_identity")
        if self.expected_turn<1:raise ValueError("invalid_expected_turn")

@dataclass(frozen=True,slots=True)
class ResolvedAction:
    """Externally calculated result applied without duplicating combat formulas."""
    actor_id:str
    target_id:str
    actor_resources:ActorResources
    target_resources:ActorResources
    metadata:Mapping[str,str|int|float|bool]

@dataclass(frozen=True,slots=True)
class BattleEvent:
    event_key:str
    battle_id:str
    turn:int
    actor_id:str|None=None
    payload:Mapping[str,str|int|float|bool]|None=None

@dataclass(frozen=True,slots=True)
class BattleAggregate:
    """Pure battle state supporting deterministic transitions and restart snapshots."""
    battle_id:str
    mode:BattleMode
    encounter_id:str|None
    actors:tuple[BattleActor,...]
    active_actor_id:str
    turn:int=1
    round_number:int=1
    status:BattleStatus=BattleStatus.ACTIVE
    terminal_claimed:bool=False
    applied_operations:tuple[str,...]=()

    def __post_init__(self)->None:
        ids=[actor.snapshot.actor_id for actor in self.actors]
        if not self.battle_id or len(ids)<2 or len(ids)!=len(set(ids)):raise ValueError("invalid_battle_identity")
        if self.active_actor_id not in ids:raise ValueError("unknown_active_actor")
        if self.turn<1 or self.round_number<1:raise ValueError("invalid_order")
        if self.mode is BattleMode.PVE and not self.encounter_id:raise ValueError("pve_requires_encounter_id")
        if self.mode is BattleMode.PVP and self.encounter_id is not None:raise ValueError("pvp_does_not_use_encounter_id")

    def actor(self,actor_id:str)->BattleActor:
        for actor in self.actors:
            if actor.snapshot.actor_id==actor_id:return actor
        raise KeyError(actor_id)

@dataclass(frozen=True,slots=True)
class BattleTransition:
    success:bool
    aggregate:BattleAggregate
    events:tuple[BattleEvent,...]=()
    failure:BattleFailure|None=None
    replayed:bool=False

def _replace_actor(aggregate:BattleAggregate,actor_id:str,resources:ActorResources)->tuple[BattleActor,...]:
    return tuple(replace(actor,resources=resources) if actor.snapshot.actor_id==actor_id else actor for actor in aggregate.actors)

def apply_resolved_action(aggregate:BattleAggregate,action:BattleAction,result:ResolvedAction,next_actor_id:str)->BattleTransition:
    """Apply a formula-free resolved action as one deterministic pure transition."""
    if action.operation_id in aggregate.applied_operations:return BattleTransition(True,aggregate,replayed=True)
    if aggregate.status is not BattleStatus.ACTIVE:return BattleTransition(False,aggregate,failure=BattleFailure.NOT_ACTIVE)
    if action.actor_id!=aggregate.active_actor_id:return BattleTransition(False,aggregate,failure=BattleFailure.WRONG_ACTOR)
    if action.expected_turn!=aggregate.turn:return BattleTransition(False,aggregate,failure=BattleFailure.STALE_TURN)
    if result.actor_id!=action.actor_id or result.target_id==result.actor_id:return BattleTransition(False,aggregate,failure=BattleFailure.INVALID_RESULT)
    try:aggregate.actor(result.target_id);aggregate.actor(next_actor_id)
    except KeyError:return BattleTransition(False,aggregate,failure=BattleFailure.INVALID_RESULT)
    actors=_replace_actor(aggregate,result.actor_id,result.actor_resources)
    interim=replace(aggregate,actors=actors)
    actors=_replace_actor(interim,result.target_id,result.target_resources)
    next_turn=aggregate.turn+1
    next_round=aggregate.round_number+(1 if next_actor_id==aggregate.actors[0].snapshot.actor_id else 0)
    updated=replace(aggregate,actors=actors,active_actor_id=next_actor_id,turn=next_turn,round_number=next_round,applied_operations=(*aggregate.applied_operations,action.operation_id))
    event=BattleEvent("TURN_RESOLVED",aggregate.battle_id,aggregate.turn,action.actor_id,dict(result.metadata))
    return BattleTransition(True,updated,(event,))

def claim_terminal(aggregate:BattleAggregate,status:BattleStatus,operation_id:str)->BattleTransition:
    """Claim victory, defeat or escape exactly once; settlement remains external."""
    if operation_id in aggregate.applied_operations:return BattleTransition(True,aggregate,replayed=True)
    if status not in {BattleStatus.VICTORY,BattleStatus.DEFEAT,BattleStatus.ESCAPED}:return BattleTransition(False,aggregate,failure=BattleFailure.INVALID_RESULT)
    if aggregate.terminal_claimed or aggregate.status is not BattleStatus.ACTIVE:return BattleTransition(False,aggregate,failure=BattleFailure.TERMINAL_ALREADY_CLAIMED)
    updated=replace(aggregate,status=status,terminal_claimed=True,applied_operations=(*aggregate.applied_operations,operation_id))
    event=BattleEvent("BATTLE_TERMINAL_CLAIMED",aggregate.battle_id,aggregate.turn,payload={"status":status.value})
    return BattleTransition(True,updated,(event,))

def to_snapshot(aggregate:BattleAggregate)->dict[str,object]:
    """Serialize stable state only; repositories own storage and transactions."""
    return {"battle_id":aggregate.battle_id,"mode":aggregate.mode.value,"encounter_id":aggregate.encounter_id,"active_actor_id":aggregate.active_actor_id,"turn":aggregate.turn,"round_number":aggregate.round_number,"status":aggregate.status.value,"terminal_claimed":aggregate.terminal_claimed,"applied_operations":list(aggregate.applied_operations),"actors":[{"actor_id":a.snapshot.actor_id,"user_id":a.snapshot.user_id,"max_hp":a.snapshot.max_hp,"max_mp":a.snapshot.max_mp,"stats":dict(a.snapshot.stats),"actor_kind":a.snapshot.actor_kind,"resources":{"hp":a.resources.hp,"mp":a.resources.mp,"rage":a.resources.rage,"energy":a.resources.energy,"combo":a.resources.combo}} for a in aggregate.actors]}

def from_snapshot(data:Mapping[str,object])->BattleAggregate:
    """Restore a validated aggregate from the canonical technical snapshot."""
    actors=[]
    for raw in data["actors"]:
        snapshot=ActorSnapshot(str(raw["actor_id"]),raw.get("user_id"),int(raw["max_hp"]),int(raw["max_mp"]),dict(raw.get("stats",{})),str(raw["actor_kind"]))
        res=raw["resources"];actors.append(BattleActor(snapshot,ActorResources(int(res["hp"]),int(res["mp"]),int(res.get("rage",0)),int(res.get("energy",0)),int(res.get("combo",0)))))
    return BattleAggregate(str(data["battle_id"]),BattleMode(str(data["mode"])),data.get("encounter_id"),tuple(actors),str(data["active_actor_id"]),int(data["turn"]),int(data["round_number"]),BattleStatus(str(data["status"])),bool(data["terminal_claimed"]),tuple(str(x) for x in data.get("applied_operations",())))
