from __future__ import annotations
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = {
    'combat_system': ROOT / 'systems' / 'combat_system.py',
    'boss_system': ROOT / 'systems' / 'boss_system.py',
    'bosses': ROOT / 'data' / 'bosses.py',
    'mobs': ROOT / 'data' / 'mobs.py',
}
for p in paths.values():
    assert p.exists(), p
    ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))

text = {k: p.read_text(encoding='utf-8-sig') for k, p in paths.items()}
findings = []

elite_function_present = 'apply_elite_modifier' in text['combat_system']
if not elite_function_present:
    findings.append('apply_elite_modifier_not_found')

# Audit-only source signals. No assumptions are made about exact current multipliers.
elite_stat_signals = {
    stat: bool(re.search(rf'\b{stat}\b', text['combat_system']))
    for stat in ('hp', 'max_hp', 'attack', 'pdef', 'mdef', 'dex')
}

boss_builder_present = 'build_location_boss' in text['boss_system']
boss_reference_signals = any(token in text['boss_system'] for token in (
    'get_mobs_for_location', 'reference_mob', 'stat_archetype', 'median',
))

proposal = {
    'normal_multiplier': 1.0,
    'elite_core_stat_multiplier_candidate': 1.5,
    'boss_core_stat_multiplier_candidate': 2.0,
    'core_stats': ['hp', 'max_hp', 'attack', 'pdef', 'mdef', 'dex'],
    'boss_reference_policy': 'deterministic same-location, same-level, same-attack-type reference profile; median when multiple mobs match',
    'random_reference_mob_for_each_encounter': False,
    'boss_unique_layer_preserved': ['skills', 'ai_weights', 'bleed_or_buffs', 'enrage', 'special_attack', 'boss_rewards'],
    'requires_separate_read_only_comparison': True,
    'requires_separate_mutation_patch': True,
}

result = {
    'version': '15.7.2.1',
    'verdict': 'PASS' if not findings else 'PASS_WITH_REVIEW',
    'elite_function_present': elite_function_present,
    'elite_stat_signals': elite_stat_signals,
    'boss_builder_present': boss_builder_present,
    'boss_already_uses_normal_reference_signals': boss_reference_signals,
    'proposal': proposal,
    'findings': findings,
    'production_files_changed': False,
    'database_writes': 0,
    'feature_gate_changed': False,
}
out = ROOT / 'reports' / 'boss_stage_15_7_2_1_reference_architecture_audit.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
assert boss_builder_present, result
print(f"[{result['verdict']}] elite/boss reference architecture audit", {
    'elite_function': elite_function_present,
    'boss_builder': boss_builder_present,
    'normal_reference_present': boss_reference_signals,
})
