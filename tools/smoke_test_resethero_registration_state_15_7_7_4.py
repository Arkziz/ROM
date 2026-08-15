from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/"handlers"/"dev.py").read_text(encoding="utf-8")
assert text.count('result = reset_hero_for_test(user_id)') == 1
assert text.count('from handlers.start import PENDING_CHARACTER_NAME') == 1
assert text.count('PENDING_CHARACTER_NAME.discard(user_id)') == 1
assert text.count('PENDING_CHARACTER_NAME.add(user_id)') == 1
assert 'user_id in bot.user_data' not in text
assert 'runtime_user_data.pop(user_id, None)' in text
print("[PASS] resethero success enters character-name input state")
