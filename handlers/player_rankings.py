# -*- coding: utf-8 -*-
from telebot import types
from systems.player_rankings_system import get_player_ranking_categories,get_player_ranking_page
RANKING_BUTTON='🏆 Рейтинг';BACK_TO_MENU='🔙 Меню'
CATEGORY_ORDER=('total_exp','gold','str','sta','dex','intelligence','wis')
LABEL_TO_KEY={value['label']:key for key,value in get_player_ranking_categories().items()}
# ROM Stage 17.33.1.2 inline category navigation
def player_rankings_exit_kb():
 kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
 kb.row(BACK_TO_MENU)
 return kb

def player_rankings_category_inline_kb():
 kb=types.InlineKeyboardMarkup()
 categories=get_player_ranking_categories()
 buttons=[types.InlineKeyboardButton(categories[key]['label'],callback_data=f'pr:category:{key}') for key in CATEGORY_ORDER]
 for index in range(0,len(buttons),2):kb.row(*buttons[index:index+2])
 return kb
def _format_value(key,value):
 if key=='gold':return f'{float(value or 0):.2f}'
 return f'{int(value or 0):,}'.replace(',',' ')
def _page_kb(data):
 kb=types.InlineKeyboardMarkup();nav=[];key=data['ranking_key'];page=data['page']
 if data['has_previous']:nav.append(types.InlineKeyboardButton('⬅️ Назад',callback_data=f'pr:{key}:{page-1}'))
 nav.append(types.InlineKeyboardButton(f"{page+1}/{data['pages']}",callback_data='pr:noop'))
 if data['has_next']:nav.append(types.InlineKeyboardButton('Далі ➡️',callback_data=f'pr:{key}:{page+1}'))
 kb.row(*nav);kb.row(types.InlineKeyboardButton('🔙 Категорії',callback_data='pr:categories'));return kb
def _build_text(data,viewer_user_id):
 category=data['category'];lines=[f"🏆 Рейтинг: {category['label']}",'']
 for row in data['items']:
  own=' 👤' if int(row['user_id'])==int(viewer_user_id) else ''
  lines.extend([f"{row['position']}. {row['character_name']}{own}",f"   Рівень: {int(row['level'])} | {category['value_label']}: {_format_value(data['ranking_key'],row['value'])}"])
 if not data['items']:lines.append('У рейтингу ще немає персонажів.')
 viewer=data.get('viewer')
 if viewer and not data.get('viewer_on_page'):
  lines.extend(['',f"Твоє місце: {viewer['position']}",f"Твоє значення: {_format_value(data['ranking_key'],viewer['value'])}"])
 return '\n'.join(lines)
def register_player_rankings_handlers(bot):
 @bot.message_handler(func=lambda m:str(getattr(m,'text','') or '')==RANKING_BUTTON)
 def rankings_menu(message):
  bot.send_message(message.chat.id,'🏆 Рейтинг гравців\n\nОберіть категорію:',reply_markup=player_rankings_exit_kb())
  bot.send_message(message.chat.id,'Оберіть категорію рейтингу:',reply_markup=player_rankings_category_inline_kb())
 @bot.message_handler(func=lambda m:str(getattr(m,'text','') or '')==BACK_TO_MENU)
 def rankings_back(message):
  from handlers.city import build_account_menu_text_17_30_1_4,account_menu_kb_17_30_1_4
  bot.send_message(message.chat.id,build_account_menu_text_17_30_1_4(message.from_user.id),reply_markup=account_menu_kb_17_30_1_4())
 @bot.callback_query_handler(func=lambda c:str(getattr(c,'data','') or '').startswith('pr:'))
 def ranking_callback(call):
  data=str(call.data or '')
  if data=='pr:noop':bot.answer_callback_query(call.id);return
  if data=='pr:categories':
   bot.edit_message_text('🏆 Рейтинг гравців\n\nОберіть категорію:',call.message.chat.id,call.message.message_id,reply_markup=player_rankings_category_inline_kb());bot.answer_callback_query(call.id);return
  if data.startswith('pr:category:'):
   key=data.split(':',2)[2];result=get_player_ranking_page(key,call.from_user.id,0)
   if not result.get('success'):bot.answer_callback_query(call.id,result.get('message','Помилка рейтингу.'),show_alert=True);return
   bot.edit_message_text(_build_text(result,call.from_user.id),call.message.chat.id,call.message.message_id,reply_markup=_page_kb(result));bot.answer_callback_query(call.id);return
  try:key,page=data.split(':')[1],int(data.split(':')[2]);result=get_player_ranking_page(key,call.from_user.id,page)
  except Exception:bot.answer_callback_query(call.id,'Некоректна сторінка.',show_alert=True);return
  if not result.get('success'):bot.answer_callback_query(call.id,result.get('message','Помилка рейтингу.'),show_alert=True);return
  bot.edit_message_text(_build_text(result,call.from_user.id),call.message.chat.id,call.message.message_id,reply_markup=_page_kb(result));bot.answer_callback_query(call.id)
