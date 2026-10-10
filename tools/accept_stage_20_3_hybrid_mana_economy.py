#!/usr/bin/env python3
"""Final executable acceptance for ROM Stage 20.3 hybrid Mana economy."""
from __future__ import annotations
import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.mana_policy import (
 MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT,MANA_REGEN_PERCENT_PER_FULL_MINUTE,
 apply_post_combat_mp_floor_value,calculate_mana_restore_amount,
 calculate_mana_skill_cost,calculate_passive_mp_regen_per_full_minute,
)
REPORTS=('reports/stage_20_3_4_pve_mana_cost_integration.json', 'reports/stage_20_3_4a_dynamic_mana_skill_descriptions.json', 'reports/stage_20_3_4b_finalize_dynamic_mana_skill_descriptions.json', 'reports/stage_20_3_5_post_combat_mana_floor.json', 'reports/stage_20_3_6_pvp_mana_policy.json', 'reports/stage_20_3_7_simulator_mana_pipeline_audit.json', 'reports/stage_20_3_7_simulator_mana_parity.json', 'reports/stage_20_3_8_legacy_mana_consolidation.json')
TESTS=('tools/smoke_test_canonical_mana_policy.py', 'tools/smoke_test_mana_skill_catalog.py', 'tools/smoke_test_pve_mana_cost_integration.py', 'tools/smoke_test_dynamic_mana_skill_descriptions.py', 'tools/smoke_test_mana_presentation_finalization.py', 'tools/smoke_test_post_combat_mana_floor.py', 'tools/smoke_test_pvp_canonical_mana_policy.py', 'tools/smoke_test_simulator_canonical_mana_policy.py', 'tools/smoke_test_legacy_mana_consolidation.py')

def main():
 assert MANA_REGEN_PERCENT_PER_FULL_MINUTE==30
 assert MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT==50
 vectors={
  'fireball':({"cost_type":"mana","mana_cost_flat":8,"mana_cost_max_mp_percent":7},[20,29,50,78]),
  'thunder':({"cost_type":"mana","mana_cost_flat":15,"mana_cost_max_mp_percent":18},[46,69,123,195]),
  'holy':({"cost_type":"mana","mana_cost_flat":6,"mana_cost_max_mp_percent":4},[13,18,30,46]),
  'blessing':({"cost_type":"mana","mana_cost_flat":12,"mana_cost_max_mp_percent":10},[29,42,72,112]),
  'purify':({"cost_type":"mana","mana_cost_flat":10,"mana_cost_max_mp_percent":8},[24,34,58,90]),
  'flow':({"cost_type":"mana","mana_cost_flat":0,"mana_cost_max_mp_percent":0},[0,0,0,0]),
 }
 maxima=(170,300,600,1000)
 for _name,(skill,expected) in vectors.items():
  assert [calculate_mana_skill_cost(skill,m) for m in maxima]==expected
 assert calculate_mana_restore_amount(170,25)==43
 assert calculate_mana_restore_amount(170,15)==26
 assert calculate_passive_mp_regen_per_full_minute(170)==51
 assert apply_post_combat_mp_floor_value(20,170)==85
 assert apply_post_combat_mp_floor_value(120,170)==120
 for rel in REPORTS:
  data=json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))
  assert data.get('status')=='PASS',(rel,data.get('status'))
 for rel in TESTS:
  q=subprocess.run([sys.executable,rel],cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True)
  assert q.returncode==0 and '[OK]' in q.stdout,(rel,q.stdout,q.stderr)
 owners={rel:(ROOT/rel).read_text(encoding='utf-8-sig') for rel in (
  'handlers/combat.py','systems/character_system.py','systems/pvp_action_validation.py',
  'systems/pvp_round_engine.py','systems/simulation/pve_battle.py',
  'systems/simulation/survival_state.py')}
 for rel,text in owners.items():ast.parse(text,filename=rel)
 assert 'calculate_mana_skill_cost' in owners['handlers/combat.py']
 assert 'calculate_mana_skill_cost' in owners['systems/pvp_action_validation.py']
 assert 'calculate_mana_skill_cost' in owners['systems/pvp_round_engine.py']
 assert 'calculate_mana_skill_cost' in owners['systems/simulation/pve_battle.py']
 assert 'calculate_mana_restore_amount' in owners['systems/pvp_round_engine.py']
 assert 'calculate_mana_restore_amount' in owners['systems/simulation/pve_battle.py']
 assert 'calculate_passive_mp_regen_per_full_minute' in owners['systems/character_system.py']
 assert 'apply_post_combat_mp_floor_value' in owners['systems/character_system.py']
 assert 'apply_post_combat_mp_floor_value' in owners['systems/simulation/survival_state.py']
 forbidden=('MP_REGEN_PERCENT_PER_MINUTE_17_15_1','MP_POST_COMBAT_FLOOR_PERCENT_17_15_1')
 for legacy in forbidden:assert legacy not in owners['systems/character_system.py']
 print('[OK] Stage 20.3 acceptance - policy, 6 skills, PvE, PvP, simulator, floor, regen and reports')
 return 0
if __name__=='__main__':raise SystemExit(main())
