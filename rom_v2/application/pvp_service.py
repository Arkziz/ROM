"""Pure PvP lifecycle orchestration; delegates all combat arithmetic to a shared resolver port."""
from dataclasses import replace
from rom_v2.domain.pvp import *
class V2PvpLifecycleService:
 def __init__(self,uow,resolver):self.uow=uow;self.resolver=resolver
 def create_from_accepted(self,battle):
  old=self.uow.by_request(battle.request_id)
  if old:return V2PvpLifecycleResult(True,"already_created",old)
  reason=self.uow.availability(battle)
  if reason:return V2PvpLifecycleResult(False,reason)
  try:
   self.uow.save(battle)
   acquired=[]
   for p in battle.participants:
    if not self.uow.acquire(p.user_id,battle.battle_id):
     for uid in acquired:self.uow.release(uid,battle.battle_id)
     cancelled=replace(battle,status=V2PvpBattleStatus.CANCELLED,result_reason="activity_session_acquire_failed");self.uow.save(cancelled);self.uow.commit();return V2PvpLifecycleResult(False,"activity_session_acquire_failed",cancelled,True)
    acquired.append(p.user_id)
   self.uow.event(battle.battle_id,"created");self.uow.commit();return V2PvpLifecycleResult(True,battle=battle,changed=True)
  except Exception:self.uow.rollback();raise
 def submit(self,action):
  b=self.uow.battle(action.battle_id)
  if not b:return V2PvpLifecycleResult(False,"battle_not_found")
  if b.status is not V2PvpBattleStatus.ACTIVE:return V2PvpLifecycleResult(False,"battle_terminal",b)
  if (action.round_number,action.revision)!=(b.round_number,b.revision):return V2PvpLifecycleResult(False,"stale_revision",b)
  if action.user_id not in {x.user_id for x in b.participants}:return V2PvpLifecycleResult(False,"not_participant",b)
  if self.uow.action(action):return V2PvpLifecycleResult(True,"already_submitted",b)
  self.uow.save_action(action);ready=self.uow.round_ready(b.battle_id,b.round_number,b.revision);self.uow.commit();return V2PvpLifecycleResult(True,battle=b,changed=True,resolution_required=ready)
 def resolve(self,battle_id,seed):
  b=self.uow.battle(battle_id)
  if not b or b.status is not V2PvpBattleStatus.ACTIVE:return V2PvpLifecycleResult(False,"battle_unavailable",b)
  if not self.uow.claim(b):return V2PvpLifecycleResult(True,"already_claimed",b)
  try:
   outcome=self.resolver.resolve(b,self.uow.actions(b))
   changed=outcome
   self.uow.save(changed);self.uow.event(battle_id,"round_resolved" if changed.status is V2PvpBattleStatus.ACTIVE else "completed")
   if changed.status is not V2PvpBattleStatus.ACTIVE:
    for p in changed.participants:self.uow.release(p.user_id,battle_id)
    self.uow.publish_history_once(changed)
   self.uow.commit();return V2PvpLifecycleResult(True,battle=changed,changed=True)
  except Exception:self.uow.release_claim(b);self.uow.rollback();raise
 def timeout(self,battle_id,missing_ids):
  b=self.uow.battle(battle_id)
  if not b or b.status is not V2PvpBattleStatus.ACTIVE:return V2PvpLifecycleResult(False,"battle_unavailable",b)
  ids={p.user_id for p in b.participants};missing=set(missing_ids)&ids
  if not missing:return V2PvpLifecycleResult(True,"no_timeout",b)
  winner=None if missing==ids else next(iter(ids-missing));reason="double_timeout" if winner is None else "forfeit_timeout";changed=replace(b,status=V2PvpBattleStatus.COMPLETED,winner_id=winner,result_reason=reason);self.uow.save(changed);self.uow.event(battle_id,reason)
  for uid in ids:self.uow.release(uid,battle_id)
  self.uow.publish_history_once(changed);self.uow.commit();return V2PvpLifecycleResult(True,battle=changed,changed=True)
 def recover(self):
  out=[]
  for b in self.uow.active():
   if self.uow.stale_claim(b):self.uow.release_claim(b)
   self.uow.reconcile(b);out.append(V2PvpRecoveryOutcome(b.battle_id,"resumed"))
  self.uow.cleanup_terminal_sessions();self.uow.commit();return tuple(out)
class InMemoryV2PvpLifecycleUow:
 def __init__(self,battles=()):self.rows={b.battle_id:b for b in battles};self.by_req={b.request_id:b for b in battles};self.actions_rows=[];self.sessions=set();self.events=[];self.history=set();self.claims=set();self.unavailable=None;self.commits=0;self.rollbacks=0
 def by_request(self,r):return self.by_req.get(r)
 def battle(self,i):return self.rows.get(i)
 def save(self,b):self.rows[b.battle_id]=b;self.by_req[b.request_id]=b
 def availability(self,b):return self.unavailable
 def acquire(self,u,b):self.sessions.add((u,b));return True
 def release(self,u,b):self.sessions.discard((u,b))
 def event(self,b,e):
  if (b,e) not in self.events:self.events.append((b,e))
 def action(self,a):return a in self.actions_rows
 def save_action(self,a):self.actions_rows.append(a)
 def round_ready(self,b,r,v):return len([a for a in self.actions_rows if (a.battle_id,a.round_number,a.revision)==(b,r,v)])==2
 def actions(self,b):return tuple(a for a in self.actions_rows if a.battle_id==b.battle_id and a.round_number==b.round_number and a.revision==b.revision)
 def claim(self,b):
  k=(b.battle_id,b.round_number,b.revision)
  if k in self.claims:return False
  self.claims.add(k);return True
 def release_claim(self,b):self.claims.discard((b.battle_id,b.round_number,b.revision))
 def publish_history_once(self,b):
  for p in b.participants:self.history.add((b.battle_id,p.user_id))
 def active(self):return tuple(b for b in self.rows.values() if b.status is V2PvpBattleStatus.ACTIVE)
 def stale_claim(self,b):return False
 def reconcile(self,b):pass
 def cleanup_terminal_sessions(self):pass
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
