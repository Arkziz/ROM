# -*- coding: utf-8 -*-
import os
from telebot import types
from systems.fatigue_artifact_system import add_fatigue_artifacts,get_total,use_fatigue_artifacts
states={}
def _kb(inv,qty,maximum):
 k=types.InlineKeyboardMarkup();k.row(types.InlineKeyboardButton('➖',callback_data=f'fa:q:{inv}:{max(1,qty-1)}'),types.InlineKeyboardButton(f'×{qty}',callback_data='fa:noop'),types.InlineKeyboardButton('➕',callback_data=f'fa:q:{inv}:{min(maximum,qty+1)}'));k.row(types.InlineKeyboardButton('✅ Використати',callback_data=f'fa:use:{inv}:{qty}'),types.InlineKeyboardButton('❌ Скасувати',callback_data='fa:cancel'));return k
def register_fatigue_artifact_handlers(bot):
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('fa:'))
 def callback(call):
  if call.data=='fa:noop':bot.answer_callback_query(call.id);return
  if call.data=='fa:cancel':bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=None);bot.answer_callback_query(call.id,'Скасовано');return
  parts=call.data.split(':');action=parts[1];inv=int(parts[2]);qty=int(parts[3]);owned=get_total(call.from_user.id)
  if action=='q':
   qty=max(1,min(qty,owned));bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=_kb(inv,qty,max(1,owned)));bot.answer_callback_query(call.id);return
  key=f'telegram:fatigue_artifact:{call.from_user.id}:{call.message.chat.id}:{call.message.message_id}';res=use_fatigue_artifacts(call.from_user.id,inv,qty,key)
  if res.get('success'):bot.edit_message_text(f"✅ Використано: 💠 Артефакт відновлення сил ×{res['used_quantity']}\n\n😴 Втома: {res['fatigue_before']} → {res['fatigue_after']}\n📦 Залишилося: ×{res['remaining']}",call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id,'Готово')
  else:bot.answer_callback_query(call.id,res['message'],show_alert=True)
 @bot.message_handler(commands=['give_fatigue_artifact'])
 def dev_grant(message):
  if str(os.getenv('DEV_MODE','')).lower() not in ('1','true','yes','on'):return
  try:qty=max(1,min(999,int(message.text.split(maxsplit=1)[1])))
  except Exception:qty=1
  res=add_fatigue_artifacts(message.from_user.id,qty);bot.send_message(message.chat.id,f"✅ DEV: видано 💠 Артефакт відновлення сил ×{res['added']}.\nЗагалом: ×{res['total']}" + (f"\nНе вмістилося: ×{res['lost']}" if res['lost'] else ''))
