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
CALLBACK_PREFIX='story_npc:'
NPC_BUTTONS={'🗣️ Староста':'elder','⚔️ Голова Найманців':'mercenary_head','⚒️ Коваль':'blacksmith'}
def _level(user_id):
 stats=get_player_stats(user_id) or {};return int(stats.get('level',1) if isinstance(stats,dict) else 1)
STATUS_LABELS={
 'LOCKED':'🔒 Недоступний','AVAILABLE':'✨ Доступний','ACTIVE':'📖 Активний',
 'COMPLETED':'✅ Виконаний','SKIPPED':'⏭️ Пропущений',
}
def _completion_button_text(quest_type):
 if quest_type=='TALK':return '✅ Продовжити'
 if quest_type=='TURN_IN':return '✅ Здати предмети'
 return '✅ Завершити квест'
def _markup(p,user_id=None,connection=None):
 kb=types.InlineKeyboardMarkup();q=p.get('quest')
 if q and p['state']=='AVAILABLE':
  kb.add(types.InlineKeyboardButton('✅ Прийняти квест',callback_data=f'{CALLBACK_PREFIX}accept:{p["npc_id"]}:{q["quest_id"]}'))
 if q and p['state']=='ACTIVE' and user_id is not None and connection is not None:
  ready=is_story_quest_objective_ready(connection,registry=STORY_QUEST_REGISTRY,user_id=int(user_id),quest_id=q['quest_id'])
  if ready:
   kb.add(types.InlineKeyboardButton(_completion_button_text(q['quest_type']),callback_data=f'{CALLBACK_PREFIX}complete:{p["npc_id"]}:{q["quest_id"]}'))
 return kb
def _text(p):
 q=p.get('quest')
 if not q:return f'{p["npc_name"]}\n\nСюжетних доручень зараз немає.'
 texts=STORY_QUEST_TEXT[q['quest_id']];definition=STORY_QUEST_REGISTRY[q['quest_id']]
 body=texts['acceptance_text'] if p['state']=='AVAILABLE' else definition.objective_text
 lines=[p['npc_name'],'',f'📜 {q["number"]}. {q["title"]}','',f'Статус: {STATUS_LABELS.get(p["state"],p["state"])}','',f'🎯 Завдання:\n{body}']
 if p['state']=='ACTIVE' and (definition.target_quantity>1 or definition.quest_type is QuestType.QUEST_ITEM):
  progress=max(int(q.get('progress',0)),int(q.get('quest_item_quantity',0)))
  lines += ['',f'📈 Прогрес:\n{min(progress,definition.target_quantity)}/{definition.target_quantity}']
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
 lines=['', '✨ Відкрито наступний квест:', f'📜 {next_quest.number}. {next_quest.title}', f'Статус: {STATUS_LABELS.get(status,status)}', '', '🎯 Наступна мета:', next_quest.objective_text]
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
def send_story_npc_if_present(bot,message,npc_id):
 p=_presentation(message.from_user.id,npc_id)
 if p.get('quest') is None:return False
 bot.send_message(message.chat.id,_text(p),reply_markup=_markup(p,user_id=message.from_user.id,connection=db.conn));return True
def register_story_quest_npc_runtime_handlers(bot):
 @bot.callback_query_handler(func=lambda c:str(getattr(c,'data','') or '').startswith(CALLBACK_PREFIX))
 def callback(call):
  try:
   _,action,npc,qid=call.data.split(':',3);uid=call.from_user.id
   if action=='accept':
    accept_story_quest_from_npc(db.conn,registry=STORY_QUEST_REGISTRY,user_id=uid,npc_id=npc,quest_id=qid,player_level=_level(uid));message='Квест прийнято.'
   elif action=='complete':
    q=STORY_QUEST_REGISTRY[qid];adapter=build_story_quest_reward_adapter(exp=q.reward.exp,gold=q.reward.gold);result=complete_active_story_quest(db.conn,registry=STORY_QUEST_REGISTRY,user_id=uid,quest_id=qid,reward_adapter=adapter,expected_turn_in_npc_id=npc);message=_completion_receipt(db.conn,uid,q,npc,result)
   else:raise ValueError('unknown story action')
   bot.answer_callback_query(call.id);bot.send_message(call.message.chat.id,message);p=_presentation(uid,npc);bot.send_message(call.message.chat.id,_text(p),reply_markup=_markup(p,user_id=uid,connection=db.conn))
  except StoryQuestCompletionError as error:
   text='❌ Завдання ще не виконано.' if 'objective is incomplete' in str(error) else '❌ Дію завершення відхилено.'
   bot.answer_callback_query(call.id,text,show_alert=True)
  except (ValueError,KeyError):
   bot.answer_callback_query(call.id,'❌ Дія недоступна.',show_alert=True)
