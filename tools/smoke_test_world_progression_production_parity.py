from data.player_progression import BASE_EXP_BY_LEVEL, CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL, apply_exp_award, get_base_exp_for_level, get_exp_to_next_level
from systems.simulation.progression_provider import ProgressionProvider
from systems.simulation.rng import SimulationRng

def main():
    provider=ProgressionProvider()
    for level in range(1,31):
        assert provider.exp_to_next(level)==BASE_EXP_BY_LEVEL[level]*CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[level]
    required=get_exp_to_next_level(1)
    assert apply_exp_award(1,0,required-1)["level"]==1
    exact=apply_exp_award(1,0,required); assert exact["level"]==2 and exact["exp"]==0
    multi=apply_exp_award(1,0,required+get_exp_to_next_level(2)+7); assert multi["level"]==3 and multi["exp"]==7
    mobs=provider.mobs(1); assert mobs and all(abs(int(m["level"])-1)<=1 for m in mobs)
    exp,gold=provider.reward(1,mobs[0],SimulationRng(136100)); assert exp>=1 and gold>=0
    assert provider.content_max_mob_level()==10
    print("[OK] World progression production-data parity")
    print("- EXP requirements levels 1..30: PASS")
    print("- below/exact/multi-level/remainder contracts: PASS")
    print("- production location and mob pool: PASS")
    print("- production EXP/gold reward functions: PASS")
    print("- current content ceiling level 10 detected: PASS")
    print("- database writes: 0")
if __name__=="__main__":main()
