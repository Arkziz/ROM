#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
updates={73: {'acceptance_text': 'Розвідники пройшли за кам’яний прохід. Це не звичайний військовий табір.\n\nУсередині яру майже немає наметів, запасів їжі або місць для відпочинку. Натомість там стоять обпалені стовпи, кам’яні чаші й дерев’яні столи, вкриті невідомими знаками.\n\nРозвідники не змогли наблизитися до столів. Місцевість досі охороняють, а предмети на них видно лише здалеку.\n\nУсе вказує на те, що сьома стоянка має інше призначення, ніж звичайні гоблінські табори.', 'completion_text': 'Голова Найманців завершує доповідь про сьому стоянку з обпаленими стовпами, кам’яними чашами та столами, вкритими невідомими знаками.'}, 76: {'acceptance_text': 'Рунний Майстер передав мені невелику пробу з таблички. У ній є подрібнений рунічний кристал, деревна смола, кров і залишки горючої олії.\n\nКоли суміш нагрівають, руна на короткий час стає активною. Але проба надто мала, щоб визначити всі її складники.\n\nЦього достатньо, щоб підтвердити: порошок готували спеціально для обряду, а його дія залежить від постійного нагрівання.'}}
for number,fields in updates.items():
 q=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==number);t=STORY_QUEST_TEXT[q.quest_id]
 for field,value in fields.items():assert t[field]==value
for number,phrases in {73: ('Потрібно знайти', 'Не бери звичайні уламки', 'Шукай те'), 76: ('Потрібен матеріал', 'Спочатку доведеться зупинити', 'підтримує вогні й охороняє чаші')}.items():
 q=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==number);t=STORY_QUEST_TEXT[q.quest_id];text=t['acceptance_text']+'\n'+t['completion_text']
 for phrase in phrases:assert phrase.casefold() not in text.casefold()
p=json.loads((ROOT/'Квести/ROM_квести_Темний_Бір_candidate.json').read_text(encoding='utf-8-sig'))
for number,fields in updates.items():
 q=next(q for q in p['quests'] if q['number']==number)
 for field,value in fields.items():assert q[field]==value
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,81))
print('PASS: Stage 19.31.4')
