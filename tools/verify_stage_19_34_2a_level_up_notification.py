#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'handlers/combat.py';s=p.read_text(encoding='utf-8-sig');ast.parse(s)
start=s.index('exp_result = reward.get("exp_result")')
end=s.index('# ==============================',start)
b=s[start:end]
assert 'level_ups > 0 and not reward_message' in b
assert '🎉 Рівень підвищено!' in b and 'Вільні очки характеристик' in b
assert b.index('bot.send_message(chat_id, reward_message)') < b.index('bot.send_message(chat_id, story_skip_message)')
assert 'story_skip_result = process_overlevel_story_quest_skip' in s
print('PASS: Stage 19.34.2a')
