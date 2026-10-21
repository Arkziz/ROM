from rom_v2.domain.combat_resources import *
def test_rage_initialization_and_canonical_gains():
 state=RageState();assert state==RageState(0,100)
 assert rage_gain_on_attack(state).state.current==15
 assert rage_gain_on_damage_taken(state).state.current==10
def test_rage_clamp_extra_gain_and_validate_before_debit():
 state=RageState(95,100);gained=rage_gain_from_skill(state,20);assert gained.state.current==100 and gained.amount==5
 failed=rage_spend(RageState(10,100),11);assert not failed.success and failed.state==RageState(10,100)
def test_energy_start_regen_clamp_and_projection():
 assert EnergyState()==EnergyState(100,100)
 state=EnergyState(70,100);regen=energy_regenerate_player_turn(state);assert regen.state.current==90 and regen.amount==20
 assert projected_energy_at_player_turn(EnergyState(95,100)).current==100
def test_energy_validate_before_debit():
 state=EnergyState(20,100);failed=energy_spend(state,21);assert not failed.success and failed.state is state
 paid=energy_spend(state,20);assert paid.success and paid.state.current==0 and paid.amount==20
