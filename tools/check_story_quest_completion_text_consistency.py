#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production text-registry regression for Stage 19.28.4."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
EXPECTED=json.loads('{"new": {"start_path_023_guards_ring": "Торговець оглядає перстень і впізнає міське клеймо. Прикраса належала одному з вартових, які готувалися до небезпечного походу.", "start_path_026_damaged_guard_shield": "Голова Найманців оглядає пошкоджений щит і помічає на ньому глибокі сліди кігтів. Доказ збережено для остаточного зіставлення, а відомості про виття біля мосту вирішено перевірити в Таверні.", "start_path_029_torn_guard_cloak": "Голова Найманців приймає клапоть плаща й порівнює його з перснем та пошкодженим щитом. Трьох доказів достатньо, щоб відновити картину нападу на патруль.", "start_path_034_runemarked_wolf_pelt": "Коваль перевіряє знайдене хутро й підтверджує, що матеріал достатньо міцний для захисних накладок. Рунічні сліди потребують обережної обробки, але зразок придатний для роботи.", "start_path_037_trail_to_the_den": "Рунний Майстер оглядає уламок і підтверджує, що позначка веде до джерела найсильнішого рунічного впливу. Слід указує на вовче лігво за кам’янистим схилом.", "start_path_043_pack_leader_seal": "Голова Найманців оглядає доказ і впізнає на ньому той самий знак, що й на каменях біля проходу. Мітка належить наближеним Ватажка та допоможе визначити, як зграя охороняє лігво."}, "unchanged": {"40": "Староста вислуховує доповідь. Лігво знайдено, шлях очищено, а мисливці готові. Голова Найманців розставить людей, Коваль завершить спорядження, а Рунний Майстер підготує захист від рунічного впливу. Староста скликає раду. Після неї почнеться останній етап походу.\\n\\n✅ Розділ «Вовча загроза» завершено.", "41": "Рішення ухвалено. Найманці перевірять підступи до лігва, а мисливці перекриють зграї шлях до відступу. Вирушай до Голови Найманців: відтепер кожен крок наближає вирішальну сутичку.", "46": "Так, це саме той слід, про який попереджав Рунний Майстер. Я позначу знахідку печаткою загону, але забирати її не буду. Віднеси матеріал Ковалеві: тепер він знатиме, що перед ним справжній доказ із лігва.", "47": "Матеріал прийнято й використано під час гартування. Сталь витримає перший удар Ватажка, а спорядження загону готове до походу. Повертайся до Голови Найманців."}}')
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
quests=sorted(STORY_QUEST_REGISTRY.values(),key=lambda q:q.number)
assert [q.number for q in quests]==list(range(1,51))
for quest_id,text in EXPECTED["new"].items():
 assert STORY_QUEST_TEXT[quest_id]["completion_text"]==text,(quest_id,STORY_QUEST_TEXT[quest_id]["completion_text"])
by_number={q.number:q for q in quests}
for number,text in EXPECTED["unchanged"].items():
 q=by_number[int(number)];assert STORY_QUEST_TEXT[q.quest_id]["completion_text"]==text,(number,STORY_QUEST_TEXT[q.quest_id]["completion_text"])
# Correct handoffs remain explicit and point to the next giver.
assert "Голови Найманців" in STORY_QUEST_TEXT[by_number[41].quest_id]["completion_text"]
assert "Ковалеві" in STORY_QUEST_TEXT[by_number[46].quest_id]["completion_text"]
assert "Голови Найманців" in STORY_QUEST_TEXT[by_number[47].quest_id]["completion_text"]
# Noun 'доповідь' is not an imperative; only verb forms are checked.
imperative=re.compile(r"\b(віднеси|передай|покажи|повернися|повертайся|звернися|вирушай|іди|принеси|доповісти)\b",re.I)
assert not imperative.search(STORY_QUEST_TEXT[by_number[40].quest_id]["completion_text"])
# Patched item endings must explain NPC interpretation/use and avoid stale handoff language.
for number in (23,26,29,34,37,43):
 text=STORY_QUEST_TEXT[by_number[number].quest_id]["completion_text"]
 assert len(re.findall(r"[\w’'-]+",text,flags=re.UNICODE))>=12
 assert not re.search(r"\b(віднеси|передай|покажи|принеси|потрібно передати)\b",text,re.I)
# All runtime completion texts remain unique and non-empty.
all_text=[str(STORY_QUEST_TEXT[q.quest_id]["completion_text"]).strip() for q in quests]
assert all(all_text) and len(all_text)==len(set(all_text))==50
print("STORY QUEST COMPLETION TEXT CONSISTENCY: PASS")
