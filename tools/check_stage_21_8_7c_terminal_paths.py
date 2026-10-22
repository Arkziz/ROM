from tests_v2.test_terminal_paths import battle
from rom_v2.domain.terminal_paths import TerminalOutcome,claim_terminal_path,can_accept_combat_action
first=claim_terminal_path(battle(),TerminalOutcome.VICTORY,"smoke")
second=claim_terminal_path(first.aggregate,TerminalOutcome.ESCAPE,"late")
assert first.accepted and first.presentation_allowed and not second.accepted and not second.events and not second.presentation_allowed and not can_accept_combat_action(first.aggregate)
print("[PASS] Stage 21.8.7c terminal paths smoke check")
