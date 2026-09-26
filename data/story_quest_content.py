"""Authoritative production story content: Start Path quests 1-10."""
from __future__ import annotations
import json
from types import MappingProxyType
from data.story_quest_definitions import NavigationDefinition,QuestItemDefinition,RequiredQuestItemDefinition,RewardDefinition,StoryQuestDefinition,QuestType,validate_story_quest_pack
_DATA=json.loads(r'''[
  {
    "definition": {
      "quest_id": "start_path_001_missing_patrol",
      "number": 1,
      "title": "Патруль не повернувся",
      "quest_type": "TALK",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": null,
      "giver_npc_id": "elder",
      "turn_in_npc_id": "elder",
      "description": "Черговий патруль не повернувся з обходу околиць. Староста просить героя почати розслідування та звернутися до Голови Найманців.",
      "objective_text": "Поговорити зі Старостою про зникнення патруля.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "elder",
        "turn_in_npc_id": "elder",
        "objective_hint": "Поговорити зі Старостою про зникнення патруля.",
        "next_step_hint": "🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста"
      }
    },
    "acceptance_text": "Кілька годин тому черговий патруль мав повернутися з обходу околиць. Вартові перевіряли стежку біля старого мосту, але від них досі немає звістки. У таборі бракує людей, а посилати ще один непідготовлений загін надто ризиковано. Поговори з Головою Найманців. Можливо, у гільдії вже щось чули про зниклих вартових.",
    "completion_text": "Староста передає короткий опис маршруту патруля та просить звернутися до Голови Найманців.",
    "progress_text": ""
  },
  {
    "definition": {
      "quest_id": "start_path_002_clear_the_path",
      "number": 2,
      "title": "Перевірка стежки",
      "quest_type": "KILL_REGION",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_001_missing_patrol",
      "giver_npc_id": "mercenary_head",
      "turn_in_npc_id": "mercenary_head",
      "description": "Голова Найманців просить розчистити околиці, щоб пошуковий загін міг безпечно пройти стежкою.",
      "objective_text": "Перемогти 3 будь-яких істот у локації Початок Шляху.",
      "target_quantity": 3,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "mercenary_head",
        "turn_in_npc_id": "mercenary_head",
        "objective_hint": "Перемогти 3 будь-яких істот у локації Початок Шляху.",
        "next_step_hint": "🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців"
      }
    },
    "acceptance_text": "Про зниклий патруль мені вже доповіли. Останніми днями звірі підходять до табору ближче, ніж зазвичай, тому пошуковий загін не зможе безпечно пройти стежкою. Розчисти околиці. Трьох перемог буде достатньо, щоб показати, що ти здатен подбати про себе за межами міста.",
    "completion_text": "Шлях до околиць став безпечнішим. Голова Найманців погоджується розповісти, що відомо гільдії.",
    "progress_text": "Перевірка стежки: {progress}/3"
  },
  {
    "definition": {
      "quest_id": "start_path_003_last_report",
      "number": 3,
      "title": "Останній слід",
      "quest_type": "TALK",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_002_clear_the_path",
      "giver_npc_id": "mercenary_head",
      "turn_in_npc_id": "mercenary_head",
      "description": "Голова Найманців повідомляє останній відомий маршрут патруля та направляє героя до старого мосту.",
      "objective_text": "Отримати від Голови Найманців відомості про останній маршрут патруля.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "mercenary_head",
        "turn_in_npc_id": "mercenary_head",
        "objective_hint": "Отримати від Голови Найманців відомості про останній маршрут патруля.",
        "next_step_hint": "🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців"
      }
    },
    "acceptance_text": "Один із мисливців бачив патруль біля старого мосту. Вартові рухалися в бік лісової стежки, хоча мали повернутися до табору іншим шляхом. На землі залишилися сліди боротьби, але мисливець не наважився йти далі сам. Перевір місцевість під час полювання. Шукай будь-який предмет, який міг належати зниклому вартовому.",
    "completion_text": "Тепер відомо, де починати пошуки: на стежці за старим мостом.",
    "progress_text": ""
  },
  {
    "definition": {
      "quest_id": "start_path_004_guard_uniform_scrap",
      "number": 4,
      "title": "Клапоть форми",
      "quest_type": "QUEST_ITEM",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_003_last_report",
      "giver_npc_id": "mercenary_head",
      "turn_in_npc_id": "elder",
      "description": "Голова Найманців просить обшукати стежку за старим мостом і пошукати будь-які сліди зниклого патруля.",
      "objective_text": "Шукати під час полювання докази, пов’язані зі зниклим патрулем.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": {
        "item_key": "start_path_guard_uniform_scrap",
        "display_name": "Клапоть форми вартового",
        "required_quantity": 1,
        "drop_chance": 0.15,
        "consume_on_completion": false
      },
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "mercenary_head",
        "turn_in_npc_id": "elder",
        "objective_hint": "Шукати під час полювання докази, пов’язані зі зниклим патрулем.",
        "next_step_hint": "🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста"
      }
    },
    "acceptance_text": "Патруль бачили біля старого мосту, але далі його слід губиться. Обшукай стежку та прилеглі хащі. Шукай будь-які речі, сліди боротьби або інші докази, які допоможуть встановити, що сталося з вартовими.",
    "completion_text": "Серед слідів вдалося знайти клапоть форми зниклого вартового. Цей доказ потрібно передати Старості.",
    "progress_text": ""
  },
  {
    "definition": {
      "quest_id": "start_path_005_evidence_from_the_trail",
      "number": 5,
      "title": "Доказ із хащі",
      "quest_type": "TURN_IN",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_004_guard_uniform_scrap",
      "giver_npc_id": "elder",
      "turn_in_npc_id": "elder",
      "description": "Показати Старості знайдений клапоть і з’ясувати, чи належав він міській варті.",
      "objective_text": "Передати Старості клапоть форми вартового.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [
        {
          "item_key": "start_path_guard_uniform_scrap",
          "quantity": 1,
          "consume": true
        }
      ],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "elder",
        "turn_in_npc_id": "elder",
        "objective_hint": "Передати Старості клапоть форми вартового.",
        "next_step_hint": "🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста"
      }
    },
    "acceptance_text": "Це частина форми нашої варти. На внутрішньому шві залишилася позначка міського складу. Отже, патруль справді дістався старого мосту. Але тканина не просто зачепилася за гілку. Її розірвано силою. Потрібно перевірити місцевість навколо мосту. Повернися до Голови Найманців і передай, що пошуки мають продовжуватися.",
    "completion_text": "Староста підтверджує, що клапоть належав міському вартовому. Зникнення патруля офіційно визнають надзвичайною подією.",
    "progress_text": ""
  },
  {
    "definition": {
      "quest_id": "start_path_006_old_bridge",
      "number": 6,
      "title": "Старий міст",
      "quest_type": "KILL_REGION",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_005_evidence_from_the_trail",
      "giver_npc_id": "mercenary_head",
      "turn_in_npc_id": "mercenary_head",
      "description": "Голова Найманців просить розчистити територію біля старого мосту, де патруль бачили востаннє.",
      "objective_text": "Перемогти 5 будь-яких істот у локації Початок Шляху.",
      "target_quantity": 5,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "mercenary_head",
        "turn_in_npc_id": "mercenary_head",
        "objective_hint": "Перемогти 5 будь-яких істот у локації Початок Шляху.",
        "next_step_hint": "🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців"
      }
    },
    "acceptance_text": "Староста передав твою знахідку. Якщо патруль атакували біля мосту, навколо можуть залишатися небезпечні істоти або нові сліди. Розчисти місцевість і не поспішай повертатися. Оглядай землю, каміння та покинуті речі.",
    "completion_text": "Територію біля старого мосту очищено. Серед слідів на землі помітний слабкий відблиск металу.",
    "progress_text": "Старий міст: {progress}/5"
  },
  {
    "definition": {
      "quest_id": "start_path_007_broken_guard_lantern",
      "number": 7,
      "title": "Згаслий ліхтар",
      "quest_type": "QUEST_ITEM",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_006_old_bridge",
      "giver_npc_id": "mercenary_head",
      "turn_in_npc_id": "blacksmith",
      "description": "Слабкий металевий відблиск біля старого мосту може виявитися новим доказом. Потрібно ретельно обшукати місцевість.",
      "objective_text": "Шукати під час полювання предмети або сліди, які могли належати зниклому патрулю.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": {
        "item_key": "start_path_broken_guard_lantern",
        "display_name": "Зламаний ліхтар вартового",
        "required_quantity": 1,
        "drop_chance": 0.15,
        "consume_on_completion": false
      },
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "mercenary_head",
        "turn_in_npc_id": "blacksmith",
        "objective_hint": "Шукати під час полювання предмети або сліди, які могли належати зниклому патрулю.",
        "next_step_hint": "🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль"
      }
    },
    "acceptance_text": "Під час зачистки біля мосту серед слідів помітили металевий відблиск. Повернися туди та уважно обшукай землю, каміння й зарості. Якщо знайдеш річ патруля, не намагайся визначати її походження самостійно.",
    "completion_text": "Серед слідів вдалося знайти зламаний ліхтар міської варти. Його потрібно показати Ковалю.",
    "progress_text": ""
  },
  {
    "definition": {
      "quest_id": "start_path_008_marks_on_metal",
      "number": 8,
      "title": "Сліди на металі",
      "quest_type": "TURN_IN",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_007_broken_guard_lantern",
      "giver_npc_id": "blacksmith",
      "turn_in_npc_id": "blacksmith",
      "description": "Показати Ковалю зламаний ліхтар і з’ясувати, де та як його пошкодили.",
      "objective_text": "Передати Ковалю зламаний ліхтар вартового.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [
        {
          "item_key": "start_path_broken_guard_lantern",
          "quantity": 1,
          "consume": true
        }
      ],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "blacksmith",
        "turn_in_npc_id": "blacksmith",
        "objective_hint": "Передати Ковалю зламаний ліхтар вартового.",
        "next_step_hint": "🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль"
      }
    },
    "acceptance_text": "Цей ліхтар належав міській варті. Я сам лагодив його минулого місяця. Подивись на корпус: метал зім’ятий, але не від падіння. Щось ударило збоку, а потім протягнуло ліхтар по камінню. На кріпленні залишився дрібний світлий пил. Такий камінь трапляється біля печер. Якщо патруль ішов далі, шукай дорогу саме туди.",
    "completion_text": "Коваль визначає, що ліхтар пошкодили неподалік кам’янистої стежки до печер.",
    "progress_text": ""
  },
  {
    "definition": {
      "quest_id": "start_path_009_path_to_the_caves",
      "number": 9,
      "title": "Шлях до печер",
      "quest_type": "KILL_REGION",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_008_marks_on_metal",
      "giver_npc_id": "mercenary_head",
      "turn_in_npc_id": "mercenary_head",
      "description": "Голова Найманців просить розчистити вузьку стежку до печер і перевірити, чи міг зниклий патруль пройти цим шляхом.",
      "objective_text": "Перемогти 6 будь-яких істот у локації Початок Шляху.",
      "target_quantity": 6,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "mercenary_head",
        "turn_in_npc_id": "mercenary_head",
        "objective_hint": "Перемогти 6 будь-яких істот у локації Початок Шляху.",
        "next_step_hint": "🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців"
      }
    },
    "acceptance_text": "Світлий пил на ліхтарі справді схожий на камінь із дороги до печер. Але пройти туди зараз непросто. Істоти заполонили вузьку стежку, а в заростях майже нічого не видно. Розчисти шлях. Якщо знайдеш нові сліди, не заходь до печер сам. Спочатку доповіси Старості.",
    "completion_text": "Стежку до печер розчищено. На вологій землі видно сліди важких чобіт, що ведуть углиб, але не повертаються назад.",
    "progress_text": "Шлях до печер: {progress}/6"
  },
  {
    "definition": {
      "quest_id": "start_path_010_investigation_begins",
      "number": 10,
      "title": "Розслідування починається",
      "quest_type": "TURN_IN",
      "location_id": "start_path",
      "unlock_level": 1,
      "previous_quest_id": "start_path_009_path_to_the_caves",
      "giver_npc_id": "elder",
      "turn_in_npc_id": "elder",
      "description": "Доповісти Старості про сліди, що ведуть до печер, і передати результати пошуків патруля.",
      "objective_text": "Доповісти Старості про дорогу до печер.",
      "target_quantity": 1,
      "boss_key": null,
      "quest_item": null,
      "required_quest_items": [],
      "quest_item_consumption": "default",
      "reward": {
        "exp": 30,
        "gold": 0.27,
        "item_keys": []
      },
      "navigation": {
        "location_id": "start_path",
        "giver_npc_id": "elder",
        "turn_in_npc_id": "elder",
        "objective_hint": "Доповісти Старості про дорогу до печер.",
        "next_step_hint": "🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста"
      }
    },
    "acceptance_text": "Сліди ведуть до печер, а патруль звідти не повернувся. Тепер зрозуміло, що випадковою затримкою це не пояснити. Я оголошую офіційне розслідування. Голова Найманців підготує пошуковий загін, а Рунний Майстер перевірить дивне світіння, яке останнім часом бачать на лісових стежках. Відпочинь і підготуй спорядження. Попереду буде складніше.",
    "completion_text": "✅ Главу «Тривога на околиці» завершено.\\n\\nСліди зниклого патруля ведуть до печер, а на стежках помічено дивне рунічне світіння.",
    "progress_text": ""
  }
]''')
def _definition(row):
 d=row["definition"]; item=d.get("quest_item"); nav=d["navigation"]
 return StoryQuestDefinition(quest_id=d["quest_id"],number=d["number"],title=d["title"],quest_type=QuestType(d["quest_type"]),location_id=d["location_id"],unlock_level=d["unlock_level"],previous_quest_id=d.get("previous_quest_id"),giver_npc_id=d["giver_npc_id"],turn_in_npc_id=d.get("turn_in_npc_id"),description=d["description"],objective_text=d["objective_text"],target_quantity=d["target_quantity"],boss_key=d.get("boss_key"),quest_item=QuestItemDefinition(**item) if item else None,required_quest_items=tuple(RequiredQuestItemDefinition(**x) for x in d.get("required_quest_items",[])),quest_item_consumption=d.get("quest_item_consumption","default"),reward=RewardDefinition(**d["reward"]),navigation=NavigationDefinition(**nav))
STORY_QUEST_REGISTRY=validate_story_quest_pack(tuple(_definition(row) for row in _DATA))
STORY_QUEST_TEXT=MappingProxyType({row["definition"]["quest_id"]:MappingProxyType({"acceptance_text":row["acceptance_text"],"completion_text":row["completion_text"],"progress_text":row["progress_text"]}) for row in _DATA})
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,11))
