#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'Квести/ROM_квести_Темний_Бір_candidate.json').read_text(encoding='utf-8-sig'))
q=next(q for q in p['quests'] if q['number']==61)
assert q['acceptance_text']=='Староста затвердив операцію. Відтепер ми не просто захищаємо старий шлях, а намагаємося зрозуміти, як працює мережа гоблінських дозорів.\n\nРозвідники нанесли на карту кілька стоянок. Окремо вони не схожі на великі табори, але між ними постійно рухаються патрулі. Один загін змінює інший, а на високих деревах чергують спостерігачі.\n\nЦі стоянки діють узгоджено. Патрулі підтримують зв’язок і контролюють внутрішні стежки значно краще, ніж ми припускали після першої розвідки.'
assert q['completion_text']=='Голова Найманців завершує доповідь про розташування внутрішніх стоянок і узгоджений рух гоблінських патрулів.'
for phrase in ('Перший удар потрібно завдати', 'під час зміни варти', 'Я покажу місце'):
 assert phrase.casefold() not in (q['description']+'\n'+q['acceptance_text']+'\n'+q['completion_text']).casefold()
assert [q['number'] for q in p['quests'] if 61<=q['number']<=70]==list(range(61,71))
assert all(q['unlock_level']==7 and q['location_id']=='dark_forest' for q in p['quests'] if 61<=q['number']<=70)
print('PASS: Stage 19.30.2')
