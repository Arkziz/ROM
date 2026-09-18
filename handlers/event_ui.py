# -*- coding: utf-8 -*-
"""Collision-safe Telegram UI for registered events."""
from telebot import types
EVENTS_BUTTON="🎉 Івенти"; PREFIX="evt:test_event_2026:"

def _active():
    from events.test_event_2026 import config
    return bool(config.ENABLED and config.is_active())
def _main_text():
    status="🟢 Івент активний" if _active() else "⏳ Івент ще не розпочався"
    return f"🎉 Тестовий івент\n\n{status}\n\nПеремагайте 🧪 Нестабільного слизня, отримуйте жетони та обмінюйте їх на пам’ятну нагороду."
def _main_kb():
    kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton("🏆 Рейтинг",callback_data=PREFIX+"rank:1"),types.InlineKeyboardButton("🛍 Крамниця",callback_data=PREFIX+"shop"));kb.add(types.InlineKeyboardButton("ℹ️ Про івент",callback_data=PREFIX+"about"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"close"));return kb
def _back():
    kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));return kb
def _edit(bot,call,text,kb):
    try: bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=kb)
    except Exception: bot.send_message(call.message.chat.id,text,reply_markup=kb)
def _rank_rows(user_id,page):
    from db_modules.connection import conn
    from systems.event_statistics_system import get_event_kill_leaderboard
    board=get_event_kill_leaderboard(conn,"test_event_2026","test_slime",page=page,user_id=user_id)
    entries=[]
    for row in board["entries"]:
        profile=conn.execute("""SELECT COALESCE(u.character_name,'Без імені'),g.name FROM users u LEFT JOIN guild_members gm ON gm.user_id=u.user_id LEFT JOIN guilds g ON g.id=gm.guild_id WHERE u.user_id=?""",(row["user_id"],)).fetchone()
        name=profile[0] if profile else "Без імені"; guild=f" [{profile[1]}]" if profile and profile[1] else ""
        entries.append(f"{row['rank']}. {name}{guild} — {row['kills']} перемог")
    own=board.get("own"); own_text="Немає зарахованих перемог." if not own else f"Ваша позиція: {own['rank']}. Перемог: {own['kills']}"
    return board,entries,own_text
def _rank_kb(page,has_next):
    kb=types.InlineKeyboardMarkup();nav=[]
    if page>1: nav.append(types.InlineKeyboardButton("◀️",callback_data=PREFIX+f"rank:{page-1}"))
    if has_next: nav.append(types.InlineKeyboardButton("▶️",callback_data=PREFIX+f"rank:{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔄 Оновити",callback_data=PREFIX+f"rank:{page}"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));return kb
def register_event_ui_handlers(bot):
    @bot.message_handler(func=lambda m: m.text==EVENTS_BUTTON)
    def open_events(message): bot.send_message(message.chat.id,_main_text(),reply_markup=_main_kb())
    @bot.callback_query_handler(func=lambda c: str(c.data or "").startswith(PREFIX))
    def event_callback(call):
        data=str(call.data or "")[len(PREFIX):];bot.answer_callback_query(call.id)
        if data=="close":
            from handlers.city import build_account_menu_text_17_30_1_4,account_menu_kb_17_30_1_4
            _edit(bot,call,build_account_menu_text_17_30_1_4(call.from_user.id),account_menu_kb_17_30_1_4());return
        if data=="home": _edit(bot,call,_main_text(),_main_kb());return
        if data=="about": _edit(bot,call,"ℹ️ Про івент\n\n🧪 Нестабільний слизень має 25% шанс зустрічі під час активного івенту. За перемогу гарантовано випадає 1 жетон. 3 жетони можна обміняти на 1 пам’ятний знак.",_back());return
        if data=="shop":
            if not _active(): _edit(bot,call,"🛍 Крамниця\n\n⏳ Івент готується. Дати проведення буде оголошено пізніше.",_back());return
            kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton("Обміняти ×1",callback_data=PREFIX+"confirm"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));_edit(bot,call,"🛍 Крамниця\n\n3 × 🧪 Експериментальний жетон → 1 × 🎁 Пам’ятний знак випробування",kb);return
        if data=="confirm":
            if not _active(): _edit(bot,call,"🛍 Крамниця\n\n⏳ Івент готується. Дати проведення буде оголошено пізніше.",_back());return
            kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton("✅ Підтвердити",callback_data=PREFIX+f"exchange:{call.message.message_id}"),types.InlineKeyboardButton("❌ Скасувати",callback_data=PREFIX+"shop"));_edit(bot,call,"Підтвердити один обмін 3 жетонів на 1 знак?",kb);return
        if data.startswith("exchange:"):
            if not _active(): _edit(bot,call,"🛍 Крамниця\n\n⏳ Івент готується. Дати проведення буде оголошено пізніше.",_back());return
            from db_modules.connection import conn
            from systems.event_shop_system import exchange_event_shop_offer
            key=f"tg:event:test_event_2026:{call.from_user.id}:{data.split(':',1)[1]}"
            try: result=exchange_event_shop_offer(conn,"test_event_2026",call.from_user.id,"test_reward_exchange",key,event_active=True);conn.commit();text="✅ Обмін виконано." if result.get("success") else "❌ Обмін недоступний."
            except ValueError as error: conn.rollback();text="❌ Недостатньо вільних жетонів або місця в сумці." if str(error) in {"insufficient_unreserved_currency","bag_full"} else "❌ Обмін не виконано."
            _edit(bot,call,text,_back());return
        if data.startswith("rank:"):
            try: page=max(1,min(10,int(data.split(":",1)[1])))
            except Exception: page=1
            board,entries,own=_rank_rows(call.from_user.id,page);body="\n".join(entries) if entries else "Рейтинг поки порожній."
            _edit(bot,call,f"🏆 Рейтинг івенту\nТоп-100, сторінка {page}/10\n\n{body}\n\n{own}",_rank_kb(page,len(entries)==10 and page<10));return
        _edit(bot,call,_main_text(),_main_kb())
