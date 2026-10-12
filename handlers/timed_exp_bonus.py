# -*- coding: utf-8 -*-
from datetime import datetime
from telebot import types
from systems.timed_exp_bonus_system import get_exp_bonus_status,preview_exp_bonus_purchase,purchase_exp_bonus
BUTTON='📈 Бонус досвіду +25%'
def _fmt(value):
 try:return datetime.fromisoformat(value).astimezone().strftime('%d.%m.%Y %H:%M')
 except Exception:return 'неактивний'
def register_timed_exp_bonus_handlers(bot):
 @bot.message_handler(func=lambda m:m.text==BUTTON)
 def open_bonus(message):
  st=get_exp_bonus_status(message.from_user.id);kb=types.InlineKeyboardMarkup(row_width=1);kb.add(types.InlineKeyboardButton('15 днів — 70 💎',callback_data='expb:preview:15'));kb.add(types.InlineKeyboardButton('30 днів — 120 💎',callback_data='expb:preview:30'));text='📈 Бонус досвіду +25%\n\nДіє лише за вбивство звичайних, елітних мобів і босів.\nДодатково +25% золота за ці перемоги.\nКонтракти та Гільдія Найманців бонус не отримують.\n\nСтатус: '+('активний до '+_fmt(st['expires_at']) if st['active'] else 'неактивний');bot.send_message(message.chat.id,text,reply_markup=kb)
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('expb:'))
 def callbacks(call):
  parts=call.data.split(':');action=parts[1];days=int(parts[2]);uid=call.from_user.id
  if action=='preview':
   p=preview_exp_bonus_purchase(uid,days)
   if not p['success']:bot.answer_callback_query(call.id,p['message'],show_alert=True);return
   kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton('✅ Придбати',callback_data=f'expb:buy:{days}'),types.InlineKeyboardButton('❌ Скасувати',callback_data=f'expb:cancel:{days}'));bot.edit_message_text(f"📈 Бонус досвіду +25%\n\nТривалість: {days} днів\nЦіна: {p['price']} 💎\nБаланс: {p['balance']} → {p['balance_after']} 💎\nДіятиме до: {_fmt(p['expires_at_after'])}\n\nБонус діє тільки за вбивство мобів.",call.message.chat.id,call.message.message_id,reply_markup=kb);bot.answer_callback_query(call.id);return
  if action=='cancel':bot.edit_message_text('❌ Покупку бонусу досвіду скасовано.',call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id);return
  key=f"telegram:exp_bonus:{uid}:{call.message.chat.id}:{call.message.message_id}:{days}";res=purchase_exp_bonus(uid,days,key)
  if res['success']:bot.edit_message_text(f"✅ Бонус досвіду +25% активовано.\n\nТривалість: {days} днів\nСписано: {res.get('price',res.get('purchase',{}).get('price_crystals'))} 💎\nБаланс: {res['balance']} 💎\nДіє до: {_fmt(res['expires_at_after'])}",call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id,'Готово')
  else:bot.answer_callback_query(call.id,res['message'],show_alert=True)
