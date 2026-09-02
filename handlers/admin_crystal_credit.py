# -*- coding: utf-8 -*-
from telebot import types
from systems.admin_crystal_credit_system import is_admin,preview_admin_adjustment,execute_admin_adjustment,get_admin_adjustment_history
states={};COMMAND='/admin_crystals'
def _menu():
 k=types.ReplyKeyboardMarkup(resize_keyboard=True);k.row('➕ Нарахувати кристали','➖ Вилучити кристали');k.row('📜 Історія адмін-операцій','❌ Закрити адмін-меню');return k
def _clear(uid):states.pop(int(uid),None)
def register_admin_crystal_credit_handlers(bot):
 @bot.message_handler(commands=['admin_crystals'])
 def open_admin(message):
  if not is_admin(message.from_user.id):return
  _clear(message.from_user.id);bot.send_message(message.chat.id,'🛡️ Адміністративні операції з кристалами',reply_markup=_menu())
 @bot.message_handler(func=lambda m:is_admin(m.from_user.id) and m.text in ('➕ Нарахувати кристали','➖ Вилучити кристали'))
 def choose(message):
  states[message.from_user.id]={'step':'target','operation':'credit' if message.text.startswith('➕') else 'debit'};bot.send_message(message.chat.id,'Введіть Telegram user ID отримувача:')
 @bot.message_handler(func=lambda m:is_admin(m.from_user.id) and m.text=='📜 Історія адмін-операцій')
 def history(message):
  result=get_admin_adjustment_history(message.from_user.id);lines=['📜 Останні адміністративні операції']
  for row in result.get('items',[]):lines.append(f"#{row['id']} | {row['operation']} | user {row['target_user_id']} | запит {row['requested_amount']} | факт {row['actual_amount']} | {row['balance_before']}→{row['balance_after']} | {row['reason']}")
  bot.send_message(message.chat.id,'\n'.join(lines),reply_markup=_menu())
 @bot.message_handler(func=lambda m:is_admin(m.from_user.id) and m.text=='❌ Закрити адмін-меню')
 def close(message):_clear(message.from_user.id);bot.send_message(message.chat.id,'✅ Адмін-меню закрито.')
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('ac:'))
 def callback(call):
  uid=call.from_user.id
  if not is_admin(uid):bot.answer_callback_query(call.id,'Доступ заборонено.',show_alert=True);return
  state=states.get(uid);data=str(call.data)
  if data=='ac:cancel':_clear(uid);bot.edit_message_text('❌ Операцію скасовано.',call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id);return
  if data.startswith('ac:confirm:'):
   nonce=data.split(':',2)[2]
   if not state or state.get('step')!='confirm' or state.get('nonce')!=nonce:bot.answer_callback_query(call.id,'Ця кнопка застаріла.',show_alert=True);return
   key=f"telegram:admin_crystal:{uid}:{call.message.chat.id}:{call.message.message_id}:{nonce}";result=execute_admin_adjustment(uid,state['target'],state['operation'],state['amount'],state['reason'],key)
   if result.get('success'):
    _clear(uid);bot.edit_message_text(f"✅ Операцію завершено.\nЗапитано: {result['requested_amount']} 💎\nФактично: {result['actual_amount']} 💎\nБаланс: {result['balance_before']} → {result['balance_after']} 💎",call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id,'Готово')
   else:bot.answer_callback_query(call.id,result.get('message','Операцію не виконано.'),show_alert=True)
 @bot.message_handler(func=lambda m:is_admin(m.from_user.id) and m.from_user.id in states)
 def input_router(message):
  uid=message.from_user.id;state=states.get(uid,{});text=str(message.text or '').strip()
  if state.get('step')=='target':
   try:state['target']=int(text)
   except Exception:bot.send_message(message.chat.id,'❌ Введіть цілий Telegram user ID.');return
   state['step']='amount';bot.send_message(message.chat.id,'Введіть кількість від 1 до 10000:');return
  if state.get('step')=='amount':
   try:state['amount']=int(text)
   except Exception:bot.send_message(message.chat.id,'❌ Введіть ціле число.');return
   state['step']='reason';bot.send_message(message.chat.id,'Введіть обов’язкову причину операції:');return
  if state.get('step')=='reason':
   state['reason']=text;preview=preview_admin_adjustment(uid,state['target'],state['operation'],state['amount'],text)
   if not preview.get('success'):_clear(uid);bot.send_message(message.chat.id,preview.get('message','Операцію не можна підготувати.'),reply_markup=_menu());return
   nonce=f"{uid:x}{message.message_id:x}";state.update({'step':'confirm','nonce':nonce});warning='\n⚠️ Буде вилучено лише доступний залишок.' if preview.get('clamped') else ''
   k=types.InlineKeyboardMarkup();k.row(types.InlineKeyboardButton('✅ Підтвердити операцію',callback_data=f'ac:confirm:{nonce}'),types.InlineKeyboardButton('❌ Скасувати',callback_data='ac:cancel'))
   bot.send_message(message.chat.id,f"🛡️ Підтвердження\n\nОперація: {preview['operation']}\nКористувач: {preview['target_user_id']}\nЗапитано: {preview['requested_amount']} 💎\nФактично: {preview['actual_amount']} 💎\nБаланс: {preview['balance_before']} → {preview['balance_after']} 💎\nПричина: {preview['reason']}{warning}",reply_markup=k)
