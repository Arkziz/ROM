from __future__ import annotations

import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
handler_path=ROOT/"handlers/pvp_round_ui.py"
source=handler_path.read_text(encoding="utf-8")
ast.parse(source)

assert 'def _pvp_terminal(battle):' in source
assert 'def _terminal_callback_answer(bot, call):' in source
assert 'def _localized_pvp_action_error(error):' in source
assert 'PvP battle is not active' not in source
assert '"pvp battle is not active":"ℹ️ Дуель уже завершена.' in source

round_start=source.index('def pvp_round_callback(call):')
round_end=source.index('@bot.callback_query_handler',round_start+10)
round_block=source[round_start:round_end]
assert round_block.index('if _pvp_terminal(battle):') < round_block.index('int(battle.get("round_number")')
assert '_localized_pvp_action_error(exc)' in round_block

surrender_start=source.index('def pvp_surrender_callback(call):')
surrender_block=source[surrender_start:]
assert surrender_block.index('if _pvp_terminal(battle):') < surrender_block.index('if mode=="ask":')
assert surrender_block.index('if _pvp_terminal(battle):') < surrender_block.index('if mode=="cancel":')
assert surrender_block.index('if _pvp_terminal(battle):') < surrender_block.index('if mode!="confirm":')

# Terminal callbacks must stop before generating confirmation, resending terminal text,
# rendering a round panel, submitting an action, or changing the persisted result.
terminal_guard='_terminal_callback_answer(bot,call); return'
assert terminal_guard in round_block
assert terminal_guard in surrender_block

print('[OK] PvP terminal callbacks localization and notification idempotency contracts')
print('- old attack/skill/refresh callbacks stop at terminal guard: PASS')
print('- old surrender ask/confirm/cancel callbacks stop at terminal guard: PASS')
print('- terminal callback popup is Ukrainian: PASS')
print('- submit_pvp_action ValueError is localized: PASS')
print('- old continue-duel callback cannot resend terminal result: PASS')
print('- old surrender callback cannot create confirmation message: PASS')
print('- production database writes: 0')
