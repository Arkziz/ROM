from rom_v2.domain.mana_engine import *
def test_max_mp_exact_terms_and_non_mana_class():
 assert mana_calculate_max_mp(1,10,10)==170
 assert mana_calculate_max_mp(50,99,99,False)==0
def test_half_up_hybrid_skill_cost_and_validation():
 assert mana_calculate_skill_cost({"mana_cost_flat":5,"mana_cost_max_mp_percent":2.5},100)==8
 try:mana_validate_skill_definition({"mana_cost_unknown":1})
 except ManaEngineError:pass
 else:raise AssertionError("unknown cost field accepted")
def test_validate_before_debit_and_restore_clamp():
 state=ManaState(10,100);failed=mana_spend(state,11);assert not failed.success and failed.state is state and failed.reason=="INSUFFICIENT_MANA"
 paid=mana_spend(state,7);assert paid.state.current_mp==3
 assert mana_restore(paid.state,200).state.current_mp==100
def test_floor_regen_and_rebase_semantics():
 assert mana_post_combat_floor(101)==51 and mana_passive_regen_tick(101)==30
 assert mana_apply_post_combat_floor(ManaState(10,101)).state.current_mp==51
 assert mana_rebase_current(80,50)==ManaState(50,50)
