from rom_v2.domain.damage_engine import *
class R:
 def __init__(self,*v):self.v=list(v)
 def random(self):return self.v.pop(0)
def test_defense_and_minimum():
 assert damage_calculate_stat_defense(10)==3.5 and damage_total_defense(5,10)==8.5
 assert damage_after_defense(10,100)==1
def test_critical_and_dodge_curves():
 assert damage_crit_chance(10)==5 and damage_crit_chance(50)==19 and damage_crit_chance(100)<60
 assert damage_dodge_chance(0,20)==1 and damage_dodge_chance(50,10)==13 and damage_dodge_chance(100,10)<50
def test_physical_magical_share_one_resolver():
 for kind in (DamageType.PHYSICAL,DamageType.MAGICAL):
  x=resolve_damage(DamageRequest(kind,20,10),R(.9,.9));assert x.damage==15 and not x.critical and not x.evaded
def test_evasion_precedes_critical_and_critical_multiplier():
 assert resolve_damage(DamageRequest(DamageType.PHYSICAL,20,0,100,100),R(0)).damage==0
 x=resolve_damage(DamageRequest(DamageType.PHYSICAL,20,0,100,0),R(.9,0));assert x.damage==30 and x.critical
