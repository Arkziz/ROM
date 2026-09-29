"""Telegram dispatch for active production story-quest NPC interactions."""
from __future__ import annotations
from telebot import types
import db
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from data.story_quest_definitions import QuestType
from data.story_quest_npcs import resolve_story_quest_navigation
from systems.story_quest_system import get_story_quest_status
from db import get_player_stats
from systems.story_quest_completion_system import StoryQuestCompletionError,complete_active_story_quest,is_story_quest_objective_ready
from systems.story_quest_npc_acceptance_system import accept_story_quest_from_npc,build_npc_story_quest_presentation
from systems.story_quest_reward_system import build_story_quest_reward_adapter
from systems.story_quest_player_level import resolve_story_quest_player_level
CALLBACK_PREFIX='sq:'
CALLBACK_ACTIONS={'accept':'a','complete':'c'}
CALLBACK_ACTIONS_REVERSE={value:key for key,value in CALLBACK_ACTIONS.items()}
def _quest_by_number(number):
 matches=[quest for quest in STORY_QUEST_REGISTRY.values() if quest.number==int(number)]
 if len(matches)!=1:raise ValueError('Невідомий або неоднозначний номер квесту.')
 return matches[0]
def _callback_data(action,npc_id,quest):
 token=CALLBACK_ACTIONS[action]
 data=f'{CALLBACK_PREFIX}{token}:{npc_id}:{quest.number}'
 if len(data.encode('utf-8'))>64:raise ValueError('Story callback перевищує ліміт Telegram.')
 return data
NPC_BUTTONS={'🗣️ Староста':'elder','⚔️ Голова Найманців':'mercenary_head','⚒️ Коваль':'blacksmith', '💠 Рунний Майстер': 'rune_master'}
def _level(user_id):
    """Resolve the player level through the canonical row-compatible adapter."""
    stats=get_player_stats(user_id)
    return resolve_story_quest_player_level(stats)
STATUS_LABELS={
 'LOCKED':'🔒 Недоступний','AVAILABLE':'✨ Доступний','ACTIVE':'📖 Активний',
 'COMPLETED':'✅ Виконаний','SKIPPED':'⏭️ Пропущений',
}
def _completion_button_text(definition):
 if definition.quest_type is QuestType.TALK:return '✅ Зрозуміло'
 if definition.quest_type is QuestType.TURN_IN:return '✅ Здати предмети'
 if definition.quest_type is QuestType.QUEST_ITEM:return '✅ Доповісти про знахідку' if (definition.turn_in_npc_id or definition.giver_npc_id)==definition.giver_npc_id else '✅ Передати доказ'
 return '✅ Завершити квест'
def _markup(p,user_id=None,connection=None):
 kb=types.InlineKeyboardMarkup();q=p.get('quest')
 if q and p['state']=='AVAILABLE':
  definition=STORY_QUEST_REGISTRY[q['quest_id']]
  label='💬 Поговорити' if definition.quest_type is QuestType.TALK else '✅ Прийняти квест'
  kb.add(types.InlineKeyboardButton(label,callback_data=_callback_data('accept',p['npc_id'],definition)))
 if q and p['state']=='ACTIVE' and user_id is not None and connection is not None:
  definition=STORY_QUEST_REGISTRY[q['quest_id']]
  completion_npc_id=definition.turn_in_npc_id or definition.giver_npc_id
  ready=is_story_quest_objective_ready(connection,registry=STORY_QUEST_REGISTRY,user_id=int(user_id),quest_id=q['quest_id'])
  if ready and p['npc_id']==completion_npc_id:
   kb.add(types.InlineKeyboardButton(_completion_button_text(definition),callback_data=_callback_data('complete',p['npc_id'],definition)))
 return kb
def _text(p):
 q=p.get('quest')
 if not q:return f'{p["npc_name"]}\n\nСюжетних доручень зараз немає.'
 texts=STORY_QUEST_TEXT[q['quest_id']];definition=STORY_QUEST_REGISTRY[q['quest_id']]
 if definition.quest_type is QuestType.TALK:
  if p['state']=='AVAILABLE':section='📖 Коротко:';body=definition.description
  elif p['state']=='ACTIVE':section='💬 Розмова:';body=texts['acceptance_text']
  else:section='🎯 Завдання:';body=definition.objective_text
 else:
  section='🎯 Завдання:';body=texts['acceptance_text'] if p['state']=='AVAILABLE' else definition.objective_text
 lines=[p['npc_name'],'',f'📜 {q["number"]}. {q["title"]}','',f'Статус: {STATUS_LABELS.get(p["state"],p["state"])}','',f'{section}\n{body}']
 if p['state']=='ACTIVE' and (definition.target_quantity>1 or definition.quest_type is QuestType.QUEST_ITEM):
  progress=max(int(q.get('progress',0)),int(q.get('quest_item_quantity',0)))
  lines += ['',f'📈 Прогрес:\n{min(progress,definition.target_quantity)}/{definition.target_quantity}']
  if definition.quest_type is QuestType.QUEST_ITEM and definition.quest_item is not None and progress>=definition.quest_item.required_quantity:
   lines += ['', '✅ Знахідку отримано:', definition.quest_item.display_name]
   completion_npc_id=definition.turn_in_npc_id or definition.giver_npc_id
   if p['npc_id']!=completion_npc_id:
    route=resolve_story_quest_navigation(completion_npc_id)
    lines += ['', '🧭 Кому передати:', route['route_text']]
 lines += ['', '🎁 Нагорода:', f'• {definition.reward.exp} EXP', f'• {float(definition.reward.gold):.2f} золота']
 return '\n'.join(lines)

def _ordered_quests():
 return tuple(sorted(STORY_QUEST_REGISTRY.values(),key=lambda quest:(quest.number,quest.quest_id)))
def _next_quest(current):
 for quest in _ordered_quests():
  if quest.number==current.number+1 and quest.previous_quest_id==current.quest_id:return quest
 return None
def _next_step_lines(connection,user_id,current,npc_id):
 next_quest=_next_quest(current)
 if next_quest is None:
  return ['', '📖 Наступна глава:', '«Рунічна аномалія»', '', 'ℹ️ Наступна глава поки не активована.'] if current.number==10 else []
 status=get_story_quest_status(connection,user_id=int(user_id),quest=next_quest,player_level=_level(user_id)).value
 lines=['', '✨ Доступний наступний квест:', f'📜 {next_quest.number}. {next_quest.title}', f'Статус: {STATUS_LABELS.get(status,status)}']
 if status=='AVAILABLE':
  if next_quest.giver_npc_id==npc_id:lines += ['', '🧭 Наступний крок:', 'Новий квест можна прийняти у цього персонажа нижче.']
  else:
   route=resolve_story_quest_navigation(next_quest.giver_npc_id)
   lines += ['', '🧭 Куди йти:', route['route_text']]
 else:
  lines += ['', '🔒 Для відкриття:', f'• досягти {next_quest.unlock_level} рівня']
 return lines
def _completion_receipt(connection,user_id,current,npc_id,result):
 texts=STORY_QUEST_TEXT[current.quest_id]
 if result.get('already_processed'):
  lines=['ℹ️ Квест уже завершено.', f'📜 {current.number}. {current.title}', '', 'Нагороду було видано раніше.']
 else:
  reward=result.get('reward') or {}
  exp=int(reward.get('exp_awarded',current.reward.exp));gold=float(reward.get('gold_awarded',current.reward.gold))
  lines=['✅ Квест завершено', '', f'📜 {current.number}. {current.title}', '', texts['completion_text'], '', '🎁 Отримано:', f'• {exp} EXP', f'• {gold:.2f} золота']
 lines += _next_step_lines(connection,user_id,current,npc_id)
 return '\n'.join(lines)
def _presentation(user_id,npc):return build_npc_story_quest_presentation(db.conn,registry=STORY_QUEST_REGISTRY,user_id=user_id,npc_id=npc,player_level=_level(user_id))
def _player_level(user_id):
    """Resolve the player level through the canonical row-compatible adapter."""
    stats=get_player_stats(user_id)
    return resolve_story_quest_player_level(stats)


def has_story_npc_if_present(message, npc_id):
    """Read-only probe used to order canonical NPC menus before story cards."""
    presentation = build_npc_story_quest_presentation(
        db.conn,
        user_id=message.from_user.id,
        player_level=_player_level(message.from_user.id),
        npc_id=npc_id,
        registry=STORY_QUEST_REGISTRY,
    )
    return presentation is not None


def send_story_npc_if_present(bot,message,npc_id):
 p=_presentation(message.from_user.id,npc_id)
 if p.get('quest') is None:return False
 bot.send_message(message.chat.id,_text(p),reply_markup=_markup(p,user_id=message.from_user.id,connection=db.conn));return True
def _required_item_display_names(definition):
    """Resolve human names of evidence required by a TURN_IN quest."""
    names=[]
    for required in definition.required_quest_items:
        display_name=None
        for candidate in STORY_QUEST_REGISTRY.values():
            item=candidate.quest_item
            if item is not None and item.item_key==required.item_key:
                display_name=item.display_name
                break
        names.append(display_name or required.item_key)
    return tuple(names)


def _turn_in_item_action_label(definition, *, active):
    """Return item-aware labels while lifecycle callbacks stay canonical."""
    if len(definition.required_quest_items)!=1:
        return '✅ Передати докази' if active else '🔍 Показати докази'
    key=definition.required_quest_items[0].item_key
    short={'start_path_guard_uniform_scrap':'клапоть','start_path_broken_guard_lantern':'ліхтар'}.get(key)
    if short is None:return '✅ Передати предмет' if active else '🔍 Показати предмет'
    return ('✅ Передати ' if active else '🔍 Показати ')+short


def _turn_in_text(presentation):
    """Show a short offer before acceptance and the NPC analysis afterwards."""
    view=presentation['quest'];definition=STORY_QUEST_REGISTRY[view['quest_id']];state=presentation['state'];texts=STORY_QUEST_TEXT[definition.quest_id]
    labels={'LOCKED':'🔒 Недоступний','AVAILABLE':'✨ Доступний','ACTIVE':'📖 Активний','COMPLETED':'✅ Виконаний','SKIPPED':'⏭️ Пропущений'}
    lines=[presentation['npc_name'],'',f'📜 {definition.number}. {definition.title}','',f"Статус: {labels.get(state,state)}",'']
    if state=='AVAILABLE':lines += ['📖 Коротко:',definition.description]
    elif state=='ACTIVE':
        lines += ['🔍 Висновок:',texts.get('acceptance_text') or definition.objective_text]
        names=_required_item_display_names(definition)
        if names:lines += ['','📦 Потрібно передати:',*[f'• {name}' for name in names]]
    else:lines += ['🎯 Завдання:',definition.objective_text]
    lines += ['','🎁 Нагорода:',f'• {definition.reward.exp} EXP',f'• {float(definition.reward.gold):.2f} золота']
    return '\n'.join(lines)


_story_text_before_turn_in_policy=_text
_story_markup_before_turn_in_policy=_markup


def _text(presentation):
    view=presentation.get('quest') or {};definition=STORY_QUEST_REGISTRY.get(view.get('quest_id'))
    if definition is not None and definition.quest_type is QuestType.TURN_IN:return _turn_in_text(presentation)
    return _story_text_before_turn_in_policy(presentation)


def _markup(presentation,user_id=None,connection=None):
    markup=_story_markup_before_turn_in_policy(presentation,user_id=user_id,connection=connection)
    view=presentation.get('quest') or {};definition=STORY_QUEST_REGISTRY.get(view.get('quest_id'))
    if definition is None or definition.quest_type is not QuestType.TURN_IN:return markup
    state=presentation.get('state')
    for row in getattr(markup,'keyboard',()):
        for button in row:
            data=getattr(button,'callback_data','') or ''
            if state=='AVAILABLE' and data.startswith('sq:a:'):button.text=_turn_in_item_action_label(definition,active=False)
            elif state=='ACTIVE' and data.startswith('sq:c:'):button.text=_turn_in_item_action_label(definition,active=True)
    return markup


def register_story_quest_npc_runtime_handlers(bot):
 @bot.callback_query_handler(func=lambda c:str(getattr(c,'data','') or '').startswith(CALLBACK_PREFIX))
 def callback(call):
  try:
   payload=call.data[len(CALLBACK_PREFIX):];token,npc,number_text=payload.split(':',2);action=CALLBACK_ACTIONS_REVERSE[token];q=_quest_by_number(number_text);qid=q.quest_id;uid=call.from_user.id
   expected_npc=q.giver_npc_id if action=='accept' else (q.turn_in_npc_id or q.giver_npc_id)
   if npc!=expected_npc:raise ValueError('NPC не відповідає цьому квесту.')
   if action=='accept':
    accept_story_quest_from_npc(db.conn,registry=STORY_QUEST_REGISTRY,user_id=uid,npc_id=npc,quest_id=qid,player_level=_level(uid));message='Розмову розпочато.' if q.quest_type is QuestType.TALK else 'Квест прийнято.'
   elif action=='complete':
    adapter=build_story_quest_reward_adapter(exp=q.reward.exp,gold=q.reward.gold);result=complete_active_story_quest(db.conn,registry=STORY_QUEST_REGISTRY,user_id=uid,quest_id=qid,reward_adapter=adapter,expected_turn_in_npc_id=npc);message=_completion_receipt(db.conn,uid,q,npc,result)
   else:raise ValueError('unknown story action')
   bot.answer_callback_query(call.id);bot.send_message(call.message.chat.id,message);p=_presentation(uid,npc);bot.send_message(call.message.chat.id,_text(p),reply_markup=_markup(p,user_id=uid,connection=db.conn))
  except StoryQuestCompletionError as error:
   text='❌ Завдання ще не виконано.' if 'objective is incomplete' in str(error) else '❌ Дію завершення відхилено.'
   bot.answer_callback_query(call.id,text,show_alert=True)
  except (ValueError,KeyError):
   bot.answer_callback_query(call.id,'❌ Дія недоступна.',show_alert=True)
