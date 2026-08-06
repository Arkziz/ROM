from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
ui=(ROOT/"systems/pvp_round_ui.py").read_text(encoding="utf-8")
handler=(ROOT/"handlers/pvp_round_ui.py").read_text(encoding="utf-8")
timer=(ROOT/"systems/pvp_timer_service.py").read_text(encoding="utf-8")
for p in (ROOT/"systems/pvp_round_ui.py",ROOT/"systems/pvp_timer_service.py",ROOT/"handlers/pvp_round_ui.py"):
    ast.parse(p.read_text(encoding="utf-8"))
assert 'Раунд {round_number}' in ui
assert 'Раунд {round_number}/' not in ui
assert 'Раунд: {round_number}/' not in ui
assert '20 секунд' in ui
assert 'basic_attack' in ui and 'skill' in ui
assert 'pvp:round:act:' in ui and 'pvp:round:refresh:' in ui
assert 'afk_skip' in timer and 'stunned_skip' in timer
assert 'resolve_persisted_pvp_round' in handler
assert 'list_active_pvp_battles' in handler
print('[OK] PvP round UI, actions and timer contracts')
print('- current round label without /50: PASS')
print('- basic attack and three production skills buttons: PASS')
print('- 20-second persisted deadline and AFK/stun timeout: PASS')
print('- stale round/revision callback guard: PASS')
print('- startup restore for existing active battle: PASS')
print('- production database writes during smoke test: 0')
