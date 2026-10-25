"""Generic Quest Engine service with exact-once planning and no content literals."""
from dataclasses import replace
from rom_v2.domain.quest_engine import *
class V2QuestEngineService:
 def __init__(self,uow,strategies):self.uow=uow;self.strategies=strategies
 def availability(self,user_id,definition,level,location_id):
  row=self.uow.progress(user_id,definition.quest_id)
  if row and row.state in {V2QuestState.COMPLETED,V2QuestState.SKIPPED}:return V2QuestResult(False,row.state.value,row)
  if self.uow.active(user_id):return V2QuestResult(False,"conflicting_active_quest")
  if location_id!=definition.location_id:return V2QuestResult(False,"wrong_location")
  if level<definition.required_level:return V2QuestResult(False,"level_required")
  if definition.previous_quest_id is not None and not self.uow.predecessor_satisfied(user_id,definition.previous_quest_id):return V2QuestResult(False,"previous_quest_required")
  return V2QuestResult(True,"available",V2QuestProgress(user_id,definition.quest_id,V2QuestState.AVAILABLE))
 def accept(self,user_id,definition,level,location_id):
  result=self.availability(user_id,definition,level,location_id)
  if not result.success:return result
  row=replace(result.progress,state=V2QuestState.ACTIVE);self.uow.save(row);self.uow.commit();return V2QuestResult(True,progress=row,changed=True)
 def apply_event(self,user_id,definition,event_key,event_id,expected_revision):
  row=self.uow.progress(user_id,definition.quest_id)
  if not row:return V2QuestResult(False,"quest_not_active",row)
  if row.revision!=expected_revision:return V2QuestResult(False,"stale_revision",row)
  # Check event identity before the state guard because the first application may
  # already have moved this quest to READY_TO_TURN_IN. Replays remain typed no-ops.
  if self.uow.event_seen(user_id,definition.quest_id,event_id):return V2QuestResult(True,"duplicate_event",row)
  if row.state is not V2QuestState.ACTIVE:return V2QuestResult(False,"quest_not_active",row)
  strategy=self.strategies[definition.objective_type];delta=strategy.progress_delta(definition,event_key,self.uow)
  if delta<=0:return V2QuestResult(False,"event_not_applicable",row)
  value=min(definition.target,row.progress+delta);state=V2QuestState.READY_TO_TURN_IN if value>=definition.target else V2QuestState.ACTIVE;changed=replace(row,progress=value,state=state,revision=row.revision+1);self.uow.record_event(user_id,definition.quest_id,event_id);self.uow.save(changed);self.uow.commit();return V2QuestResult(True,progress=changed,changed=True)
 def turn_in(self,user_id,definition,expected_revision):
  row=self.uow.progress(user_id,definition.quest_id);key=(definition.quest_id,user_id,expected_revision)
  if self.uow.reward_recorded(key):return V2QuestResult(True,"already_completed",self.uow.progress(user_id,definition.quest_id))
  if not row or row.state is not V2QuestState.READY_TO_TURN_IN:return V2QuestResult(False,"not_ready",row)
  if row.revision!=expected_revision:return V2QuestResult(False,"stale_revision",row)
  try:
   if definition.required_item_quantity:self.uow.consume_items(user_id,definition.required_item_key,definition.required_item_quantity)
   self.uow.plan_reward(user_id,definition.reward,key);done=replace(row,state=V2QuestState.COMPLETED,revision=row.revision+1);self.uow.save(done);self.uow.record_reward(key);self.uow.commit();return V2QuestResult(True,progress=done,changed=True,reward_planned=True)
  except Exception:self.uow.rollback();raise
 def skip(self,user_id,definition,expected_revision):
  row=self.uow.progress(user_id,definition.quest_id)
  if row and row.state is V2QuestState.SKIPPED:return V2QuestResult(True,"already_skipped",row)
  if not row or row.state is not V2QuestState.ACTIVE or row.revision!=expected_revision:return V2QuestResult(False,"skip_not_allowed",row)
  skipped=replace(row,state=V2QuestState.SKIPPED,revision=row.revision+1);self.uow.save(skipped);self.uow.commit();return V2QuestResult(True,progress=skipped,changed=True)
class InMemoryV2QuestEngineUow:
 def __init__(self):self.rows={};self.events=set();self.rewards=set();self.reward_plans=[];self.items={};self.commits=0;self.rollbacks=0
 def progress(self,u,q):return self.rows.get((u,q))
 def active(self,u):return next((x for (uid,_),x in self.rows.items() if uid==u and x.state in {V2QuestState.ACTIVE,V2QuestState.READY_TO_TURN_IN}),None)
 def predecessor_satisfied(self,u,q):
  x=self.progress(u,q);return bool(x and x.state in {V2QuestState.COMPLETED,V2QuestState.SKIPPED})
 def save(self,x):self.rows[(x.user_id,x.quest_id)]=x
 def event_seen(self,u,q,e):return (u,q,e) in self.events
 def record_event(self,u,q,e):self.events.add((u,q,e))
 def reward_recorded(self,k):return k in self.rewards
 def record_reward(self,k):self.rewards.add(k)
 def consume_items(self,u,k,n):
  if self.items.get((u,k),0)<n:raise ValueError("quest_items_missing")
  self.items[(u,k)]-=n
 def plan_reward(self,u,r,k):self.reward_plans.append((u,r,k))
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
