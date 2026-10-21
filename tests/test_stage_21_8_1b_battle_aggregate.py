from rom_v2.domain.battle import *
def battle(mode=BattleMode.PVE):
 a=BattleActor(ActorSnapshot("player",1,100,50,{"patk":10},"player"),ActorResources(100,50))
 b=BattleActor(ActorSnapshot("enemy",None,80,0,{"pdef":2},"enemy"),ActorResources(80,0))
 return BattleAggregate("b1",mode,"enc1" if mode is BattleMode.PVE else None,(a,b),"player")
def test_pure_deterministic_transition_and_replay():
 b=battle();a=BattleAction("op1","player",BattleActionKind.ATTACK,1);r=ResolvedAction("player","enemy",ActorResources(100,50),ActorResources(70,0),{"damage":10});x=apply_resolved_action(b,a,r,"enemy");assert x.success and x.aggregate.actor("enemy").resources.hp==70 and b.actor("enemy").resources.hp==80;assert apply_resolved_action(x.aggregate,a,r,"enemy").replayed
def test_wrong_actor_and_stale_turn_rejected_without_mutation():
 b=battle();r=ResolvedAction("enemy","player",ActorResources(80,0),ActorResources(90,50),{});x=apply_resolved_action(b,BattleAction("x","enemy",BattleActionKind.ATTACK,1),r,"player");assert x.failure is BattleFailure.WRONG_ACTOR and x.aggregate is b
def test_terminal_single_claim_without_reward_settlement():
 b=battle();x=claim_terminal(b,BattleStatus.VICTORY,"done");assert x.success and x.aggregate.terminal_claimed;assert claim_terminal(x.aggregate,BattleStatus.DEFEAT,"other").failure is BattleFailure.TERMINAL_ALREADY_CLAIMED;assert x.events[0].payload=={"status":"VICTORY"}
def test_snapshot_round_trip_and_mode_identity():
 for mode in (BattleMode.PVE,BattleMode.PVP):
  b=battle(mode);assert from_snapshot(to_snapshot(b))==b
