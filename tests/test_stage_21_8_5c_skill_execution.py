from rom_v2.domain.skill_execution import *
class Resource:
 def __init__(self,n):self.n=n;self.payments=[]
 def can_pay(self,c):return self.n>=c
 def pay(self,c):self.n-=c;self.payments.append(c)
class Cooldowns:
 def __init__(self):self.data={};self.starts=[]
 def remaining(self,k):return self.data.get(k,0)
 def start(self,k,n):self.data[k]=n;self.starts.append((k,n))
def policies(resource=None,cooldowns=None):
 r=resource or Resource(100);c=cooldowns or Cooldowns();return r,c,lambda s:True,lambda s,d:True,lambda s,d:{"damage":7},lambda cls:DamageType.MAGICAL if cls=="mage" else DamageType.PHYSICAL
def test_basic_attack_uses_class_router_and_zero_cost():
 r,c,a,h,e,route=policies();out=execute_skill(SkillRequest("basic","mage"),{"basic":SkillDefinition("basic",SkillKind.BASIC_ATTACK)},r,c,a,h,e,route);assert out.success and out.damage_type is DamageType.MAGICAL and r.payments==[0]
def test_active_skill_validates_then_mutates_exactly_once():
 r,c,a,h,e,route=policies();s=SkillDefinition("slash",SkillKind.ACTIVE,10,3,DamageType.PHYSICAL);out=execute_skill(SkillRequest("slash","warrior"),{"slash":s},r,c,a,h,e,route);assert out.success and r.n==90 and r.payments==[10] and c.starts==[("slash",3)]
def test_failures_do_not_partially_mutate():
 for reason,setup in [(FailureReason.UNKNOWN_SKILL,{}),(FailureReason.INSUFFICIENT_RESOURCE,{"resource":Resource(0)}),(FailureReason.ON_COOLDOWN,{"cooldowns":Cooldowns()})]:
  r=setup.get("resource",Resource(100));c=setup.get("cooldowns",Cooldowns());s=SkillDefinition("x",SkillKind.ACTIVE,5,2,DamageType.PHYSICAL)
  if reason is FailureReason.ON_COOLDOWN:c.data["x"]=1
  a,h,e,route=(lambda s:True),(lambda s,d:True),(lambda s,d:{"damage":1}),(lambda cls:DamageType.PHYSICAL)
  out=execute_skill(SkillRequest("missing" if reason is FailureReason.UNKNOWN_SKILL else "x","warrior"),{"x":s},r,c,a,h,e,route);assert out.failure is reason and r.payments==[] and c.starts==[]
def test_miss_and_rejected_effect_do_not_pay_or_cooldown():
 for hit,effect,reason in [(False,{"damage":1},FailureReason.MISS),(True,None,FailureReason.EFFECT_REJECTED)]:
  r,c,a,_,_,route=policies();s=SkillDefinition("x",SkillKind.ACTIVE,5,2,DamageType.MAGICAL);out=execute_skill(SkillRequest("x","mage"),{"x":s},r,c,a,lambda s,d:hit,lambda s,d:effect,route);assert out.failure is reason and not r.payments and not c.starts
if __name__=="__main__":
 test_basic_attack_uses_class_router_and_zero_cost()
 test_active_skill_validates_then_mutates_exactly_once()
 test_failures_do_not_partially_mutate()
 test_miss_and_rejected_effect_do_not_pay_or_cooldown()
 print("[PASS] Stage 21.8.5c targeted contract tests")
