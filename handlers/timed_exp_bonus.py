# -*- coding: utf-8 -*-
from datetime import datetime
from telebot import types
from systems.timed_exp_bonus_system import get_exp_bonus_status,preview_exp_bonus_purchase,purchase_exp_bonus
BUTTON='💎 Premium: +25% досвіду та золота'
def _format_premium_expiration_kyiv(value):
 """Render a UTC string or datetime in the approved Kyiv presentation format."""
 try:
  from datetime import datetime as _datetime, timezone as _timezone
  from zoneinfo import ZoneInfo
  if isinstance(value, _datetime):
   parsed=value
  else:
   parsed=_datetime.fromisoformat(str(value or '').replace('Z','+00:00'))
  if parsed.tzinfo is None:
   parsed=parsed.replace(tzinfo=_timezone.utc)
  return parsed.astimezone(ZoneInfo('Europe/Kyiv')).strftime('%d.%m.%Y %H:%M за Києвом')
 except Exception:
  return 'час завершення невідомий'
def register_timed_exp_bonus_handlers(bot):
 @bot.message_handler(func=lambda m:m.text==BUTTON)
 def open_bonus(message):
  st=get_exp_bonus_status(message.from_user.id);kb=types.InlineKeyboardMarkup(row_width=1);kb.add(types.InlineKeyboardButton('15 днів — 100 💎',callback_data='expb:preview:15'));kb.add(types.InlineKeyboardButton('30 днів — 180 💎',callback_data='expb:preview:30'));text='💎 Premium-бонус\n\nПід час перемоги над звичайними, елітними мобами та босами ти отримуєш:\n\n• +25% досвіду;\n• +25% золота.\n\nPremium не збільшує нагороди за квести, контракти, продаж предметів, аукціон, адміністративні операції та нагороди гільдії.\n\nСтатус: '+('активний до '+_format_premium_expiration_kyiv(st['expires_at']) if st['active'] else 'неактивний');bot.send_message(message.chat.id,text,reply_markup=kb)
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('expb:'))
 def callbacks(call):
  parts=call.data.split(':');action=parts[1];days=int(parts[2]);uid=call.from_user.id
  if action=='preview':
   p=preview_exp_bonus_purchase(uid,days)
   if not p['success']:bot.answer_callback_query(call.id,p['message'],show_alert=True);return
   kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton('✅ Придбати',callback_data=f'expb:buy:{days}'),types.InlineKeyboardButton('❌ Скасувати',callback_data=f'expb:cancel:{days}'));bot.edit_message_text(f"💎 Premium-бонус\n\nПід час перемоги над звичайними, елітними мобами та босами ти отримуєш:\n\n• +25% досвіду;\n• +25% золота.\n\nPremium не збільшує нагороди за квести, контракти, продаж предметів, аукціон, адміністративні операції та нагороди гільдії.\n\nТривалість: {days} днів\nЦіна: {p['price']} 💎\nБаланс: {p['balance']} → {p['balance_after']} 💎\nДіятиме до: {_format_premium_expiration_kyiv(p['expires_at_after'])}",call.message.chat.id,call.message.message_id,reply_markup=kb);bot.answer_callback_query(call.id);return
  if action=='cancel':bot.edit_message_text('❌ Покупку бонусу досвіду скасовано.',call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id);return
  key=f"telegram:exp_bonus:{uid}:{call.message.chat.id}:{call.message.message_id}:{days}";res=purchase_exp_bonus(uid,days,key)
  if res['success']:bot.edit_message_text(f"✅ 💎 Premium-бонус активовано.\n\n+25% досвіду та +25% золота за перемогу над мобами.\n\nТривалість: {days} днів\nСписано: {res.get('price',res.get('purchase',{}).get('price_crystals'))} 💎\nБаланс: {res['balance']} 💎\nДіє до: {_format_premium_expiration_kyiv(res['expires_at_after'])}",call.message.chat.id,call.message.message_id);bot.answer_callback_query(call.id,'Готово')
  else:bot.answer_callback_query(call.id,res['message'],show_alert=True)
