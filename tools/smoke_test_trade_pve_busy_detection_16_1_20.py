from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import handlers.player_interaction as interaction

class FakeBot:
    def __init__(self, user_data):
        self.user_data = user_data

original = getattr(interaction, "_PLAYER_INTERACTION_COMBAT_BOT", None)
try:
    interaction._PLAYER_INTERACTION_COMBAT_BOT = FakeBot({})
    assert interaction._possible_pve_busy(101) is False
    assert interaction._possible_pve_busy(202) is False

    interaction._PLAYER_INTERACTION_COMBAT_BOT = FakeBot({101: {"hp": 10}})
    assert interaction._possible_pve_busy(101) is True
    assert interaction._possible_pve_busy(202) is False

    interaction._PLAYER_INTERACTION_COMBAT_BOT = FakeBot({"303": {"hp": 10}})
    assert interaction._possible_pve_busy(303) is True
finally:
    if original is None:
        interaction.__dict__.pop("_PLAYER_INTERACTION_COMBAT_BOT", None)
    else:
        interaction._PLAYER_INTERACTION_COMBAT_BOT = original

source = (ROOT / "handlers" / "player_interaction.py").read_text(encoding="utf-8")
assert 'any(token in low for token in ("battle","combat","fight"))' not in source
assert '_PLAYER_INTERACTION_COMBAT_BOT = bot' in source
print("[PASS] trade PvE busy checker uses exact bot.user_data membership")
