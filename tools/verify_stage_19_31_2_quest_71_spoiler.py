#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'Квести/ROM_квести_Темний_Бір_candidate.json').read_text(encoding='utf-8-sig'))
q=next(x for x in p['quests'] if x['number']==71)
assert q['acceptance_text']=='Ми зіставили сім зарубок на жетоні з відомими стежками. Шість маршрутів ведуть до стоянок, які розвідники вже бачили. Остання стежка проходить через стару вирубку й зникає біля кам’яного яру.\n\nУночі над деревами в тому напрямку видно червоне світло, а вітер приносить запах диму. До яру регулярно прямують озброєні гобліни.\n\nЦе перший маршрут, який не збігається з жодною відомою стоянкою. Отже, за кам’яним яром прихована частина мережі, якої ще немає на наших картах.' and q['completion_text']=='Голова Найманців завершує доповідь про невідомий маршрут, що проходить через стару вирубку до кам’яного яру.'
text=q['description']+'\n'+q['acceptance_text']+'\n'+q['completion_text']
for phrase in ('Відтисни гоблінські загони', 'відкрий прохід для розвідників', 'Не заходь за кам’яний прохід'):assert phrase.casefold() not in text.casefold()
b=[x for x in p['quests'] if 71<=x['number']<=80]
assert [x['number'] for x in b]==list(range(71,81))
assert all(x['unlock_level']==8 and x['reward']['exp']==87 and float(x['reward']['gold'])==3.23 for x in b)
print('PASS: Stage 19.31.2')
