# -*- coding: utf-8 -*-
from telebot import types
from keyboards import main_kb
from systems.crystal_shop_system import CRYSTAL_SHOP_CATALOG,get_crystal_shop_catalog,preview_crystal_shop_purchase,purchase_crystal_shop_item
from systems.crystal_wallet_system import get_crystal_balance
MENU_BUTTON='📋 Меню';SHOP_BUTTON='💎 Магазин кристалів';BACK='🔙 Закрити магазин';states={}
def _menu_kb():
 k=types.ReplyKeyboardMarkup(resize_keyboard=True);k.add(SHOP_BUTTON);k.add(BACK);return k
def _shop_kb():
 k=types.ReplyKeyboardMarkup(resize_keyboard=True)
 for iid,v in get_crystal_shop_catalog().items():k.add(f"{v['name']} — {v['price']} 💎")
 k.add(BACK);return k
def _qty_kb(iid,qty):
 k=types.InlineKeyboardMarkup();k.row(types.InlineKeyboardButton('➖',callback_data=f'cs:q:{iid}:{max(1,qty-1)}'),types.InlineKeyboardButton(f'×{qty}',callback_data='cs:noop'),types.InlineKeyboardButton('➕',callback_data=f'cs:q:{iid}:{qty+1}'));k.row(types.InlineKeyboardButton('✍️ Ввести кількість',callback_data=f'cs:input:{iid}'));k.row(types.InlineKeyboardButton('✅ Продовжити',callback_data=f'cs:review:{iid}:{qty}'),types.InlineKeyboardButton('❌ Скасувати',callback_data='cs:cancel'));return k
def _item_from_text(text):
 for iid,v in CRYSTAL_SHOP_CATALOG.items():
  if str(text or '').startswith(v['name']):return iid
 return None

def _remember_shop_message(user_id, chat_id, message_id, item_id, quantity, stage):
    states[int(user_id)] = {
        "chat_id": int(chat_id),
        "message_id": int(message_id),
        "item_id": int(item_id),
        "quantity": int(quantity),
        "stage": str(stage),
    }


def _close_shop_session(bot, user_id, text="❌ Вибір покупки закрито."):
    state = states.pop(int(user_id), None)
    if not state:
        return False
    try:
        bot.edit_message_text(
            text,
            int(state["chat_id"]),
            int(state["message_id"]),
            reply_markup=None,
        )
    except Exception:
        try:
            bot.edit_message_reply_markup(
                int(state["chat_id"]),
                int(state["message_id"]),
                reply_markup=None,
            )
        except Exception:
            pass
    return True


def _active_shop_callback(call, *, item_id=None, quantity=None, stages=()):
    state = states.get(int(call.from_user.id))
    if not state:
        return False
    if int(state.get("chat_id", -1)) != int(call.message.chat.id):
        return False
    if int(state.get("message_id", -1)) != int(call.message.message_id):
        return False
    if item_id is not None and int(state.get("item_id", -1)) != int(item_id):
        return False
    if quantity is not None and int(state.get("quantity", -1)) != int(quantity):
        return False
    if stages and str(state.get("stage")) not in set(stages):
        return False
    return True


def _reject_stale_shop_callback(bot, call):
    try:
        bot.answer_callback_query(
            call.id,
            "Це меню покупки вже неактивне.",
            show_alert=True,
        )
    except Exception:
        pass


def register_crystal_shop_handlers(bot):
 @bot.message_handler(func=lambda m:m.text==MENU_BUTTON)
 def menu(message):
  _close_shop_session(bot,message.from_user.id)
  bot.send_message(message.chat.id,'📋 Меню\n\nОберіть розділ:',reply_markup=_menu_kb())
 @bot.message_handler(func=lambda m:m.text==SHOP_BUTTON)
 def shop(message):
  _close_shop_session(bot,message.from_user.id)
  bot.send_message(message.chat.id,f"💎 Магазин кристалів\n\nБаланс: {get_crystal_balance(message.from_user.id)} 💎\n\nОберіть предмет:",reply_markup=_shop_kb())
 @bot.message_handler(func=lambda m:m.text==BACK)
 def back(message):
  _close_shop_session(bot,message.from_user.id)
  bot.send_message(message.chat.id,'Головне меню.',reply_markup=main_kb())
 @bot.message_handler(func=lambda m:_item_from_text(m.text) is not None)
 def choose(message):
  iid=_item_from_text(message.text)
  _close_shop_session(bot,message.from_user.id)
  v=CRYSTAL_SHOP_CATALOG[iid]
  sent=bot.send_message(message.chat.id,f"{v['name']}\nЦіна: {v['price']} 💎\nКількість: 1\nРазом: {v['price']} 💎",reply_markup=_qty_kb(iid,1))
  _remember_shop_message(message.from_user.id,sent.chat.id,sent.message_id,iid,1,'quantity')
 @bot.callback_query_handler(func=lambda c:str(c.data or '').startswith('cs:'))
 def callback(call):
  data=call.data;uid=call.from_user.id
  if data=='cs:noop':bot.answer_callback_query(call.id);return
  if data=='cs:cancel':
   if not _active_shop_callback(call,stages=('quantity','confirm')):
    _reject_stale_shop_callback(bot,call);return
   _close_shop_session(bot,uid,'❌ Покупку скасовано.')
   bot.answer_callback_query(call.id,'Скасовано');return
  parts=data.split(':');action=parts[1]
  if action=='q':
   iid=int(parts[2]);qty=max(1,min(999,int(parts[3])))
   if not _active_shop_callback(call,item_id=iid,stages=('quantity',)):
    _reject_stale_shop_callback(bot,call);return
   _remember_shop_message(uid,call.message.chat.id,call.message.message_id,iid,qty,'quantity')
   v=CRYSTAL_SHOP_CATALOG[iid];bot.edit_message_text(f"{v['name']}\nЦіна: {v['price']} 💎\nКількість: {qty}\nРазом: {v['price']*qty} 💎",call.message.chat.id,call.message.message_id,reply_markup=_qty_kb(iid,qty));bot.answer_callback_query(call.id);return
  if action=='input':
   iid=int(parts[2])
   if not _active_shop_callback(call,item_id=iid,stages=('quantity',)):
    _reject_stale_shop_callback(bot,call);return
   msg=bot.send_message(call.message.chat.id,'✍️ Введіть кількість від 1 до 999:');bot.register_next_step_handler(msg,manual_quantity,iid,call.message.message_id);bot.answer_callback_query(call.id);return
  if action=='review':
   iid=int(parts[2]);qty=int(parts[3])
   if not _active_shop_callback(call,item_id=iid,quantity=qty,stages=('quantity',)):
    _reject_stale_shop_callback(bot,call);return
   p=preview_crystal_shop_purchase(uid,iid,qty)
   if not p['success']:bot.answer_callback_query(call.id,p['message'],show_alert=True);return
   k=types.InlineKeyboardMarkup();k.row(types.InlineKeyboardButton('✅ Підтвердити покупку',callback_data=f'cs:buy:{iid}:{qty}'),types.InlineKeyboardButton('❌ Скасувати',callback_data='cs:cancel'));bot.edit_message_text(f"✅ Підтвердження покупки\n\n{p['name']}\nКількість: {qty}\nЦіна за 1: {p['unit_price']} 💎\nРазом: {p['total_price']} 💎\nБаланс: {p['balance']} → {p['balance_after']} 💎",call.message.chat.id,call.message.message_id,reply_markup=k);_remember_shop_message(uid,call.message.chat.id,call.message.message_id,iid,qty,'confirm');bot.answer_callback_query(call.id);return
  if action=='buy':
   iid=int(parts[2]);qty=int(parts[3])
   if not _active_shop_callback(call,item_id=iid,quantity=qty,stages=('confirm',)):
    _reject_stale_shop_callback(bot,call);return
   key=f"telegram:crystal_shop:{uid}:{call.message.chat.id}:{call.message.message_id}";res=purchase_crystal_shop_item(uid,iid,qty,key)
   if res['success']:
    _close_shop_session(bot,uid,f"✅ Покупку завершено.\n\n{res.get('name',CRYSTAL_SHOP_CATALOG[iid]['name'])} ×{qty}\nСписано: {res.get('total_price',CRYSTAL_SHOP_CATALOG[iid]['price']*qty)} 💎\nБаланс: {res.get('balance',res.get('purchase',{}).get('balance_after'))} 💎");bot.answer_callback_query(call.id,'Готово')
   else:bot.answer_callback_query(call.id,res['message'],show_alert=True)
 def manual_quantity(message,iid,source_message_id):
  try:qty=int(str(message.text).strip())
  except Exception:bot.send_message(message.chat.id,'❌ Введіть ціле число від 1 до 999.');return
  if qty<1 or qty>999:bot.send_message(message.chat.id,'❌ Кількість має бути від 1 до 999.');return
  state=states.get(message.from_user.id)
  if not state or int(state.get('message_id',-1))!=int(source_message_id) or int(state.get('item_id',-1))!=int(iid) or state.get('stage')!='quantity':
   bot.send_message(message.chat.id,'Це меню покупки вже неактивне.');return
  v=CRYSTAL_SHOP_CATALOG[iid];sent=bot.send_message(message.chat.id,f"{v['name']}\nЦіна: {v['price']} 💎\nКількість: {qty}\nРазом: {v['price']*qty} 💎",reply_markup=_qty_kb(iid,qty))
  _close_shop_session(bot,message.from_user.id)
  _remember_shop_message(message.from_user.id,sent.chat.id,sent.message_id,iid,qty,'quantity')
