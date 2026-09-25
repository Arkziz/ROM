"""Telegram dispatch for active production story-quest NPC interactions."""
from __future__ import annotations
from telebot import types
import db
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from data.story_quest_definitions import QuestType
from db import get_player_stats
from systems.story_quest_completion_system import StoryQuestCompletionError,complete_active_story_quest
from systems.story_quest_npc_acceptance_system import accept_story_quest_from_npc,build_npc_story_quest_presentation
from systems.story_quest_reward_system import build_story_quest_reward_adapter
CALLBACK_PREFIX='story_npc:'
NPC_BUTTONS={'🗣️ Староста':'elder','⚔️ Голова Найманців':'mercenary_head','⚒️ Коваль':'blacksmith'}
def _level(user_id):
 stats=get_player_stats(user_id) or {};return int(stats.get('level',1) if isinstance(stats,dict) else 1)
def _markup(p):
 kb=types.InlineKeyboardMarkup()
 q=p.get('quest')
 if q and p['state']=='AVAILABLE':kb.add(types.InlineKeyboardButton('✅ Прийняти квест',callback_data=f'{CALLBACK_PREFIX}accept:{p["npc_id"]}:{q["quest_id"]}'))
 if q and p['state']=='ACTIVE' and q['quest_type'] in {'TALK','TURN_IN','QUEST_ITEM','KILL_REGION'}:kb.add(types.InlineKeyboardButton('✅ Завершити квест',callback_data=f'{CALLBACK_PREFIX}complete:{p["npc_id"]}:{q["quest_id"]}'))
 return kb
def _text(p):
 q=p.get('quest')
 if not q:return f'{p["npc_name"]}\n\nСюжетних доручень зараз немає.'
 texts=STORY_QUEST_TEXT[q['quest_id']];definition=STORY_QUEST_REGISTRY[q['quest_id']];body=texts['acceptance_text'] if p['state']=='AVAILABLE' else definition.objective_text;return f'{p["npc_name"]}\n\n📜 {q["number"]}. {q["title"]}\n\n{body}\n\nСтатус: {p["state"]}'
def _presentation(user_id,npc):return build_npc_story_quest_presentation(db.conn,registry=STORY_QUEST_REGISTRY,user_id=user_id,npc_id=npc,player_level=_level(user_id))
def send_story_npc_if_present(bot,message,npc_id):
 p=_presentation(message.from_user.id,npc_id)
 if p.get('quest') is None:return False
 bot.send_message(message.chat.id,_text(p),reply_markup=_markup(p));return True
def register_story_quest_npc_runtime_handlers(bot):
 @bot.callback_query_handler(func=lambda c:str(getattr(c,'data','') or '').startswith(CALLBACK_PREFIX))
 def callback(call):
  try:
   _,action,npc,qid=call.data.split(':',3);uid=call.from_user.id
   if action=='accept':
    accept_story_quest_from_npc(db.conn,registry=STORY_QUEST_REGISTRY,user_id=uid,npc_id=npc,quest_id=qid,player_level=_level(uid));message='Квест прийнято.'
   elif action=='complete':
    q=STORY_QUEST_REGISTRY[qid];adapter=build_story_quest_reward_adapter(exp=q.reward.exp,gold=q.reward.gold);result=complete_active_story_quest(db.conn,registry=STORY_QUEST_REGISTRY,user_id=uid,quest_id=qid,reward_adapter=adapter,expected_turn_in_npc_id=npc);message=STORY_QUEST_TEXT[qid]['completion_text'] if not result['already_processed'] else 'Квест уже завершено.'
   else:raise ValueError('unknown story action')
   bot.answer_callback_query(call.id);bot.send_message(call.message.chat.id,message);p=_presentation(uid,npc);bot.send_message(call.message.chat.id,_text(p),reply_markup=_markup(p))
  except (ValueError,KeyError,StoryQuestCompletionError) as error:bot.answer_callback_query(call.id,f'Дія недоступна: {error}',show_alert=True)
