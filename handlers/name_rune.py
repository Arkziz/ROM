# -*- coding: utf-8 -*-
from telebot import types
from systems.name_rune_system import NAME_RUNE_ITEM_ID,get_name_rune_inventory,preview_name_change,rename_with_name_rune
states={}
def register_name_rune_handlers(bot):
 def begin(chat_id,user_id,inventory_id=None):
  rune=get_name_rune_inventory(user_id)
  if not rune or (inventory_id is not None and int(rune['id'])!=int(inventory_id)):
   bot.send_message(chat_id,'❌ ✍️ Руну імені не знайдено в інвентарі.');return
  states[user_id]={'stage':'input','inventory_id':int(rune['id'])};msg=bot.send_message(chat_id,'✍️ Введіть нове ім’я персонажа:');bot.register_next_step_handler(msg,input_name)
 @bot.message_handler(commands=['name_rune'])
 def start(message):begin(message.chat.id,message.from_user.id)
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('name_rune_use:'))
 def inventory_use(call):
  try:inventory_id=int(call.data.split(':',1)[1])
  except Exception:bot.answer_callback_query(call.id,'Некоректна дія.',show_alert=True);return
  bot.answer_callback_query(call.id);begin(call.message.chat.id,call.from_user.id,inventory_id)
 def input_name(message):
  uid=message.from_user.id;state=states.get(uid)
  if not state or state.get('stage')!='input':return
  p=preview_name_change(uid,message.text,inventory_id=state['inventory_id'])
  if not p['success']:states.pop(uid,None);bot.send_message(message.chat.id,'❌ '+p['message']);return
  if int(p['inventory_id'])!=int(state['inventory_id']):states.pop(uid,None);bot.send_message(message.chat.id,'❌ Це меню вже неактивне.');return
  states[uid]={'stage':'confirm','new_name':p['new_name'],'inventory_id':int(p['inventory_id'])};kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton('✅ Підтвердити',callback_data='nr:confirm'),types.InlineKeyboardButton('❌ Скасувати',callback_data='nr:cancel'));sent=bot.send_message(message.chat.id,f"✍️ Зміна імені персонажа\n\nПоточне ім’я: {p['old_name']}\nНове ім’я: {p['new_name']}\n\nБуде використано:\n✍️ Руна імені ×1",reply_markup=kb);states[uid].update(chat_id=sent.chat.id,message_id=sent.message_id)
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('nr:'))
 def callback(call):
  uid=call.from_user.id;state=states.get(uid)
  if not state or state.get('stage')!='confirm' or state.get('message_id')!=call.message.message_id:bot.answer_callback_query(call.id,'Це меню вже неактивне.',show_alert=True);return
  if call.data=='nr:cancel':states.pop(uid,None);bot.edit_message_text('❌ Зміну імені скасовано.',call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id);return
  rune=get_name_rune_inventory(uid)
  if not rune or int(rune['id'])!=int(state['inventory_id']):states.pop(uid,None);bot.answer_callback_query(call.id,'Це меню вже неактивне.',show_alert=True);return
  key=f"telegram:name_rune:{uid}:{call.message.chat.id}:{call.message.message_id}";result=rename_with_name_rune(uid,state['new_name'],key,inventory_id=state['inventory_id'])
  if result['success']:states.pop(uid,None);bot.edit_message_text(f"✅ Ім’я персонажа змінено.\n\n{result.get('old_name',result.get('change',{}).get('old_name'))} → {result.get('new_name',result.get('change',{}).get('new_name'))}",call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id,'Готово')
  else:bot.answer_callback_query(call.id,result['message'],show_alert=True)
