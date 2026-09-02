# -*- coding: utf-8 -*-
from telebot import types
from datetime import datetime
from zoneinfo import ZoneInfo
from systems.admin_crystal_credit_system import is_admin,preview_admin_adjustment,execute_admin_adjustment,get_admin_adjustment_history
states={};COMMAND='/admin_crystals'
def _menu():
 k=types.ReplyKeyboardMarkup(resize_keyboard=True);k.row('➕ Нарахувати кристали','➖ Вилучити кристали');k.row('📜 Історія адмін-операцій','❌ Закрити адмін-меню');return k
def _clear(uid):states.pop(int(uid),None)
def _history_text(result):
 lines=['📜 Історія адміністративних операцій']
 if not result.get('items'):return '\n\n'.join((lines[0],'Операцій ще немає.'))
 for row in result['items']:
  operation='➕ Нарахування' if row['operation']=='credit' else '➖ Вилучення'
  created=datetime.fromisoformat(row['created_at']).astimezone(ZoneInfo('Europe/Kyiv')).strftime('%d.%m.%Y %H:%M')
  block=[f"#{row['id']} · {operation}",f"👤 Користувач: {row['target_user_id']}",f"💎 Запитано: {row['requested_amount']}",f"✅ Фактично: {row['actual_amount']}",f"💰 Баланс: {row['balance_before']} → {row['balance_after']}",f"📝 Причина: {row['reason']}",f"🕒 {created}"]
  if row['operation']=='debit' and row['actual_amount']<row['requested_amount']:block.append('⚠️ Вилучено лише доступний залишок')
  lines.append('\n'.join(block))
 return '\n\n'.join(lines)
def _history_kb(result):
 k=types.InlineKeyboardMarkup();buttons=[];page=int(result.get('page',0));total_pages=max(1,int(result.get('total_pages',1)))
 if page>0:buttons.append(types.InlineKeyboardButton('⬅️ Назад',callback_data=f'ac:history:{page-1}'))
 buttons.append(types.InlineKeyboardButton(f'{page+1}/{total_pages}',callback_data='ac:noop'))
 if result.get('has_next'):buttons.append(types.InlineKeyboardButton('Далі ➡️',callback_data=f'ac:history:{page+1}'))
 k.row(*buttons);k.row(types.InlineKeyboardButton('❌ Закрити історію',callback_data='ac:history_close'));return k
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
  result=get_admin_adjustment_history(message.from_user.id,page=0,page_size=10);bot.send_message(message.chat.id,_history_text(result),reply_markup=_history_kb(result))
 @bot.message_handler(func=lambda m:is_admin(m.from_user.id) and m.text=='❌ Закрити адмін-меню')
 def close(message):
  _clear(message.from_user.id)
  from handlers.city import build_account_menu_text_17_30_1_4,account_menu_kb_17_30_1_4
  bot.send_message(message.chat.id,build_account_menu_text_17_30_1_4(message.from_user.id),reply_markup=account_menu_kb_17_30_1_4())
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('ac:'))
 def callback(call):
  uid=call.from_user.id
  if not is_admin(uid):bot.answer_callback_query(call.id,'Доступ заборонено.',show_alert=True);return
  state=states.get(uid);data=str(call.data)
  if data=='ac:noop':bot.answer_callback_query(call.id);return
  if data=='ac:history_close':bot.edit_message_text('✅ Історію закрито.',call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id);return
  if data.startswith('ac:history:'):
   page=max(0,int(data.rsplit(':',1)[1]));result=get_admin_adjustment_history(uid,page=page,page_size=10);bot.edit_message_text(_history_text(result),call.message.chat.id,call.message.message_id,reply_markup=_history_kb(result));bot.answer_callback_query(call.id);return
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
