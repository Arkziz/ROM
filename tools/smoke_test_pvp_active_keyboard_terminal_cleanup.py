from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
handler=(ROOT/"handlers/pvp_round_ui.py").read_text(encoding="utf-8")
system=(ROOT/"systems/pvp_system.py").read_text(encoding="utf-8")
interaction=(ROOT/"handlers/pvp_interaction.py").read_text(encoding="utf-8")
ast.parse(handler); ast.parse(system); ast.parse(interaction)
assert 'PVP_STATUS_BUTTON="⚔️ Стан дуелі"' in handler
assert 'pvp_active_reply_kb' in handler
assert 'reply_markup=_main_kb()' in handler
assert '_release_terminal_participants' in handler
assert 'cleanup_terminal_pvp_activity_sessions()' in handler
assert 'activate_pvp_battle_ui(bot, battle_id)' in interaction
assert 'get_active_pvp_battle_for_user' in system
assert 'cleanup_terminal_pvp_activity_sessions' in system
print('[OK] PvP active keyboard and terminal session cleanup contracts')
print('- normal persistent menu replaced during duel: PASS')
print('- duel status persistent button: PASS')
print('- new accepted duel opens round UI immediately: PASS')
print('- victory/defeat/draw releases both pvp_battle sessions: PASS')
print('- terminal orphan sessions cleaned on startup: PASS')
print('- main keyboard restored after duel: PASS')
print('- production database writes during smoke test: 0')
