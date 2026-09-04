# -*- coding: utf-8 -*-
from telebot import types
from data.about_game import ABOUT_GAME_INTRO,ABOUT_GAME_SECTION_ORDER,ABOUT_GAME_SECTIONS,build_about_game_section_text
ABOUT_GAME_BUTTON="📖 Про гру";ABOUT_CALLBACK_PREFIX="about:"
def _registered(uid):
 from db import needs_character_name,needs_character_class
 return not needs_character_name(uid) and not needs_character_class(uid)
def _about_menu_kb():
 k=types.InlineKeyboardMarkup();buttons=[types.InlineKeyboardButton(ABOUT_GAME_SECTIONS[key]["button"],callback_data=f"about:section:{key}") for key in ABOUT_GAME_SECTION_ORDER]
 for i in range(0,len(buttons),2):k.row(*buttons[i:i+2])
 k.row(types.InlineKeyboardButton("❌ Закрити",callback_data="about:close"));return k
def _section_kb(key):
 i=ABOUT_GAME_SECTION_ORDER.index(key);k=types.InlineKeyboardMarkup();row=[]
 if i>0:row.append(types.InlineKeyboardButton("⬅️ Попередній",callback_data=f"about:section:{ABOUT_GAME_SECTION_ORDER[i-1]}"))
 row.append(types.InlineKeyboardButton("📖 До розділів",callback_data="about:menu"))
 if i+1<len(ABOUT_GAME_SECTION_ORDER):row.append(types.InlineKeyboardButton("Наступний ➡️",callback_data=f"about:section:{ABOUT_GAME_SECTION_ORDER[i+1]}"))
 k.row(*row);k.row(types.InlineKeyboardButton("❌ Закрити",callback_data="about:close"));return k
def _return_account_menu(bot,chat_id,uid,message_id):
 from handlers.city import build_account_menu_text_17_30_1_4,account_menu_kb_17_30_1_4
 try:bot.edit_message_reply_markup(chat_id,message_id,reply_markup=None)
 except Exception:pass
 bot.send_message(chat_id,build_account_menu_text_17_30_1_4(uid),reply_markup=account_menu_kb_17_30_1_4())
def register_about_game_handlers(bot):
 @bot.message_handler(func=lambda m:str(getattr(m,"text","") or "")==ABOUT_GAME_BUTTON)
 def open_about(message):
  if not _registered(message.from_user.id):bot.send_message(message.chat.id,"❗ Спочатку завершіть створення персонажа.");return
  bot.send_message(message.chat.id,ABOUT_GAME_INTRO,reply_markup=_about_menu_kb())
 @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","") or "").startswith(ABOUT_CALLBACK_PREFIX))
 def about_callback(call):
  if not _registered(call.from_user.id):bot.answer_callback_query(call.id,"Спочатку завершіть створення персонажа.",show_alert=True);return
  data=str(call.data or "")
  if data=="about:menu":bot.edit_message_text(ABOUT_GAME_INTRO,call.message.chat.id,call.message.message_id,reply_markup=_about_menu_kb());bot.answer_callback_query(call.id);return
  if data=="about:close":bot.answer_callback_query(call.id);_return_account_menu(bot,call.message.chat.id,call.from_user.id,call.message.message_id);return
  if data.startswith("about:section:"):
   key=data.split(":",2)[2];text=build_about_game_section_text(key)
   if text is None or key not in ABOUT_GAME_SECTION_ORDER:bot.answer_callback_query(call.id,"Розділ не знайдено.",show_alert=True);return
   bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=_section_kb(key));bot.answer_callback_query(call.id);return
  bot.answer_callback_query(call.id,"Ця кнопка застаріла.",show_alert=True)
