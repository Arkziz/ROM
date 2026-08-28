import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
city=(R/'handlers/city.py').read_text(encoding='utf-8');combat=(R/'handlers/combat.py').read_text(encoding='utf-8');system=(R/'systems/timed_exp_bonus_system.py').read_text(encoding='utf-8')
for s in (city,combat,system):ast.parse(s)
assert '💎 Premium: активний' in city and '💎 Premium: неактивний' in city
assert '📈 Бонус за вбивство мобів: +25% EXP' in city
assert 'Дата реєстрації: {_format_account_utc_17_30_1_1' in city
assert 'Premium +25%: +{premium_bonus} EXP' in combat
assert 'Базовий:' in combat and 'Прогрес:' in combat
assert 'premium_exp_bonus' in combat and 'exp_bonus_active' in combat
assert 'get_exp_bonus_account_summary' in system
print('[PASS] Stage 17.30.1.1 menu status and reward breakdown contracts')
