#!/usr/bin/env python3
"""Structural and pure acceptance checks for Stage 20.3.8 consolidation."""
from __future__ import annotations
import ast,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.mana_policy import (
 MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT,
 MANA_REGEN_PERCENT_PER_FULL_MINUTE,
 apply_post_combat_mp_floor_value,
 calculate_mana_restore_amount,
 calculate_mana_skill_cost,
 calculate_passive_mp_regen_per_full_minute,
)

def main():
 assert MANA_REGEN_PERCENT_PER_FULL_MINUTE==30
 assert MANA_POST_COMBAT_FLOOR_CURRENT_PERCENT==50
 assert calculate_passive_mp_regen_per_full_minute(170)==51
 assert calculate_mana_restore_amount(170,25)==43
 assert calculate_mana_restore_amount(170,15)==26
 assert apply_post_combat_mp_floor_value(20,170)==85
 assert apply_post_combat_mp_floor_value(120,170)==120
 owners={
  'character':(ROOT/'systems/character_system.py').read_text(encoding='utf-8-sig'),
  'pve':(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig'),
  'pvp_validation':(ROOT/'systems/pvp_action_validation.py').read_text(encoding='utf-8-sig'),
  'pvp_engine':(ROOT/'systems/pvp_round_engine.py').read_text(encoding='utf-8-sig'),
  'simulator':(ROOT/'systems/simulation/pve_battle.py').read_text(encoding='utf-8-sig'),
  'survival':(ROOT/'systems/simulation/survival_state.py').read_text(encoding='utf-8-sig'),
 }
 for name,text in owners.items(): ast.parse(text,filename=name)
 character=owners['character'];compact=''.join(character.split())
 assert 'MP_REGEN_PERCENT_PER_MINUTE_17_15_1' not in character
 assert 'MP_POST_COMBAT_FLOOR_PERCENT_17_15_1' not in character
 assert 'calculate_passive_mp_regen_per_full_minute(maximum)' in character
 assert 'apply_post_combat_mp_floor_value(current,maximum)' in compact
 assert 'calculate_mana_skill_cost' in owners['pve']
 assert 'calculate_mana_skill_cost' in owners['pvp_validation']
 assert 'calculate_mana_skill_cost' in owners['pvp_engine']
 assert 'calculate_mana_skill_cost' in owners['simulator']
 assert 'calculate_mana_restore_amount' in owners['pvp_engine']
 assert 'calculate_mana_restore_amount' in owners['simulator']
 assert 'apply_post_combat_mp_floor_value(self.mp,self.max_mp)' in ''.join(owners['survival'].split())
 pvp_compact=''.join(owners['pvp_engine'].split())
 simulator_compact=''.join(owners['simulator'].split())
 character_compact=''.join(owners['character'].split())
 forbidden_exact=(
  'round(actor.max_mp*0.25)',
  'round(actor.max_mp*0.15)',
  'round(player.max_resource*.25)',
  'round(player.max_resource*.15)',
  'maximum*0.30',
  'maximum*.30',
 )
 for legacy in forbidden_exact:
  assert legacy not in pvp_compact,legacy
  assert legacy not in simulator_compact,legacy
  assert legacy not in character_compact,legacy
 print('[OK] Legacy Mana consolidation - one policy owner across PvE, PvP, simulator, regen and floor')
 return 0
if __name__=='__main__':raise SystemExit(main())
