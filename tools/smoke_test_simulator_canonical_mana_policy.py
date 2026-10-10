#!/usr/bin/env python3
"""Pure/structural acceptance checks for simulator canonical Mana parity."""
from __future__ import annotations
import importlib,inspect,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.mana_policy import apply_post_combat_mp_floor_value,calculate_mana_restore_amount,calculate_mana_skill_cost

def main():
 fire={"cost_type":"mana","cost":999,"mana_cost_flat":8,"mana_cost_max_mp_percent":7}
 thunder={"cost_type":"mana","cost":999,"mana_cost_flat":15,"mana_cost_max_mp_percent":18}
 assert [calculate_mana_skill_cost(fire,m) for m in (170,300,600,1000)]==[20,29,50,78]
 assert [calculate_mana_skill_cost(thunder,m) for m in (170,300,600,1000)]==[46,69,123,195]
 assert calculate_mana_restore_amount(170,25)==43
 assert calculate_mana_restore_amount(170,15)==26
 assert apply_post_combat_mp_floor_value(20,170)==85
 assert apply_post_combat_mp_floor_value(120,170)==120
 battle=(ROOT/'systems/simulation/pve_battle.py').read_text(encoding='utf-8-sig')
 survival=(ROOT/'systems/simulation/survival_state.py').read_text(encoding='utf-8-sig')
 assert battle.count('calculate_mana_skill_cost(skill, actor.max_resource)')==1
 assert battle.count('self._effective_skill_cost(actor, skill)')==2
 assert battle.count('calculate_mana_restore_amount')>=3
 assert 'round(player.max_resource*.25)' not in ''.join(battle.split())
 assert 'round(player.max_resource*.15)' not in ''.join(battle.split())
 assert 'apply_post_combat_mp_floor_value(self.mp, self.max_mp)' in survival
 start=survival.index('def restore_mp_after_combat')
 end=survival.find('\n    def ',start+1)
 method=survival[start:] if end<0 else survival[start:end]
 assert 'self.mp=self.max_mp' not in ''.join(method.split())
 assert 'apply_post_combat_mp_floor_value(self.mp,self.max_mp)' in ''.join(method.split())
 print('[OK] Simulator Mana parity - dynamic cost, half-up restore and 50% non-additive floor')
 return 0
if __name__=='__main__':raise SystemExit(main())
