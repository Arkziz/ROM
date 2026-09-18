# -*- coding: utf-8 -*-
"""Collision-safe Telegram event UI with explicit message ownership."""
from telebot import types
from datetime import datetime,timezone
EVENTS_BUTTON="🎉 Івенти";EXIT_BUTTON="🔙 Вийти з івентів";PREFIX="evt:test_event_2026:"
_ACTIVE_EVENT_UI={}

def _active():
    from events.test_event_2026 import config
    return bool(config.ENABLED and config.is_active())
def _scope_kb():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True);kb.add(EXIT_BUTTON);return kb
def _main_text():
    status="🟢 Івент активний" if _active() else "⏳ Івент ще не розпочався"
    return f"🎉 Тестовий івент\n\n{status}\n\nПеремагайте 🧪 Нестабільного слизня, отримуйте жетони та обмінюйте їх на пам’ятну нагороду."
# ROM_STAGE_18_29_4F_EVENT_ARCHIVE
ARCHIVE_PAGE_SIZE=5
def _archive_rows():
    import events
    events.load_event_modules()
    rows=[]
    now=datetime.now(timezone.utc)
    status_order={"active":0,"upcoming":1,"completed":2}
    for module in events.get_registered_events():
        cfg=module.config;start=getattr(cfg,"START_AT",None);end=getattr(cfg,"END_AT",None)
        if start is None or end is None:status="upcoming"
        elif cfg.is_active(now):status="active"
        elif now>=end:status="completed"
        else:status="upcoming"
        rows.append({"event_key":cfg.EVENT_KEY,"title":getattr(cfg,"TITLE",cfg.EVENT_KEY),"status":status,"start":start,"end":end,"completed_read_only":status=="completed"})
    return sorted(rows,key=lambda x:(status_order[x["status"]],x["start"] or datetime.max.replace(tzinfo=timezone.utc),x["event_key"]))
def _archive_kb(rows,page,total_pages):
    kb=types.InlineKeyboardMarkup()
    for row in rows:kb.add(types.InlineKeyboardButton(("✅ " if row["completed_read_only"] else "⏳ ")+row["title"],callback_data=PREFIX+"archive:view:"+row["event_key"]))
    nav=[]
    if page>1:nav.append(types.InlineKeyboardButton("◀️",callback_data=PREFIX+f"archive:list:{page-1}"))
    if page<total_pages:nav.append(types.InlineKeyboardButton("▶️",callback_data=PREFIX+f"archive:list:{page+1}"))
    if nav:kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));return kb
def _archive_text(page):
    rows=_archive_rows();pages=max(1,(len(rows)+ARCHIVE_PAGE_SIZE-1)//ARCHIVE_PAGE_SIZE);page=max(1,min(pages,page));chunk=rows[(page-1)*ARCHIVE_PAGE_SIZE:page*ARCHIVE_PAGE_SIZE]
    body="\n".join(f"{i}. {r['title']} — {r['status']}" for i,r in enumerate(chunk,(page-1)*ARCHIVE_PAGE_SIZE+1)) or "Архів поки порожній."
    return f"📚 Архів івентів\nСторінка {page}/{pages}\n\n{body}",chunk,page,pages
def _main_kb():
    kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton("🏆 Рейтинг",callback_data=PREFIX+"rank:1"),types.InlineKeyboardButton("🛍 Крамниця",callback_data=PREFIX+"shop"));kb.add(types.InlineKeyboardButton("ℹ️ Про івент",callback_data=PREFIX+"about"));kb.add(types.InlineKeyboardButton("📚 Архів",callback_data=PREFIX+"archive:list:1"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"close"));return kb
def _back():
    kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));return kb
def _delete(bot,chat_id,message_id):
    if not chat_id or not message_id:return
    try:bot.delete_message(int(chat_id),int(message_id));return
    except Exception:pass
    try:bot.edit_message_reply_markup(int(chat_id),int(message_id),reply_markup=None)
    except Exception:pass
def _close(bot,user_id,chat_id):
    state=_ACTIVE_EVENT_UI.pop(int(user_id),None) or {}
    _delete(bot,state.get("chat_id") or chat_id,state.get("card_message_id"))
    _delete(bot,state.get("chat_id") or chat_id,state.get("scope_message_id"))
    from handlers.city import build_account_menu_text_17_30_1_4,account_menu_kb_17_30_1_4
    bot.send_message(chat_id,build_account_menu_text_17_30_1_4(user_id),reply_markup=account_menu_kb_17_30_1_4())
def _valid(call):
    state=_ACTIVE_EVENT_UI.get(int(call.from_user.id))
    return bool(state and int(state.get("chat_id"))==int(call.message.chat.id) and int(state.get("card_message_id"))==int(call.message.message_id))
def _edit(bot,call,text,kb):
    uid=int(call.from_user.id);state=_ACTIVE_EVENT_UI.get(uid)
    if not state or not _valid(call):return False
    try:
        bot.edit_message_text(text,int(call.message.chat.id),int(call.message.message_id),reply_markup=kb)
        return True
    except Exception:pass
    sent=bot.send_message(int(call.message.chat.id),text,reply_markup=kb)
    old_id=state.get("card_message_id")
    state["card_message_id"]=int(sent.message_id)
    _delete(bot,state.get("chat_id"),old_id)
    return True
def _rank_rows(user_id,page):
    from db_modules.connection import conn
    from systems.event_statistics_system import get_event_kill_leaderboard
    board=get_event_kill_leaderboard(conn,"test_event_2026","test_slime",page=page,user_id=user_id);entries=[]
    for row in board["entries"]:
        profile=conn.execute("""SELECT COALESCE(u.character_name,'Без імені'),g.name FROM users u LEFT JOIN guild_members gm ON gm.user_id=u.user_id LEFT JOIN guilds g ON g.id=gm.guild_id WHERE u.user_id=?""",(row["user_id"],)).fetchone()
        name=profile[0] if profile else "Без імені";guild=f" [{profile[1]}]" if profile and profile[1] else "";entries.append(f"{row['rank']}. {name}{guild} — {row['kills']} перемог")
    own=board.get("own");own_text="Немає зарахованих перемог." if not own else f"Ваша позиція: {own['rank']}. Перемог: {own['kills']}"
    return entries,own_text
def _rank_kb(page,has_next):
    kb=types.InlineKeyboardMarkup();nav=[]
    if page>1:nav.append(types.InlineKeyboardButton("◀️",callback_data=PREFIX+f"rank:{page-1}"))
    if has_next:nav.append(types.InlineKeyboardButton("▶️",callback_data=PREFIX+f"rank:{page+1}"))
    if nav:kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔄 Оновити",callback_data=PREFIX+f"rank:{page}"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));return kb
def register_event_ui_handlers(bot):
    @bot.message_handler(func=lambda m:m.text==EVENTS_BUTTON)
    def open_events(message):
        uid=int(message.from_user.id);old=_ACTIVE_EVENT_UI.pop(uid,None) or {}
        _delete(bot,old.get("chat_id"),old.get("card_message_id"));_delete(bot,old.get("chat_id"),old.get("scope_message_id"))
        scope=bot.send_message(message.chat.id,"🎉 Розділ івентів",reply_markup=_scope_kb())
        card=bot.send_message(message.chat.id,_main_text(),reply_markup=_main_kb())
        _ACTIVE_EVENT_UI[uid]={"chat_id":int(message.chat.id),"scope_message_id":int(scope.message_id),"card_message_id":int(card.message_id)}
    @bot.message_handler(func=lambda m:m.text==EXIT_BUTTON)
    def event_reply_exit(message):
        if int(message.from_user.id) not in _ACTIVE_EVENT_UI:return
        _close(bot,message.from_user.id,message.chat.id)
    @bot.callback_query_handler(func=lambda c:str(c.data or "").startswith(PREFIX))
    def event_callback(call):
        if not _valid(call):bot.answer_callback_query(call.id,"Це меню вже неактивне.",show_alert=False);return
        data=str(call.data or "")[len(PREFIX):];bot.answer_callback_query(call.id)
        if data=="close":_close(bot,call.from_user.id,call.message.chat.id);return
        if data=="home":_edit(bot,call,_main_text(),_main_kb());return
        if data.startswith("archive:list:"):
            try:page=int(data.rsplit(":",1)[1])
            except Exception:page=1
            text,rows,page,pages=_archive_text(page);_edit(bot,call,text,_archive_kb(rows,page,pages));return
        if data.startswith("archive:view:"):
            key=data.split(":",2)[2];row=next((x for x in _archive_rows() if x["event_key"]==key),None)
            if not row or not row["completed_read_only"]:_edit(bot,call,"📚 Архів івентів\n\nЦей івент ще не завершено.",_back());return
            kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton("🏆 Історичний рейтинг",callback_data=PREFIX+"rank:1"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"archive:list:1"));_edit(bot,call,f"📚 {row['title']}\n\nСтатус: завершено\nАрхів доступний лише для перегляду.",kb);return
        if data=="about":_edit(bot,call,"ℹ️ Про івент\n\n🧪 Нестабільний слизень має 25% шанс зустрічі під час активного івенту. За перемогу гарантовано випадає 1 жетон. 3 жетони можна обміняти на 1 пам’ятний знак.",_back());return
        if data=="shop":
            if not _active():_edit(bot,call,"🛍 Крамниця\n\n⏳ Івент готується. Дати проведення буде оголошено пізніше.",_back());return
            kb=types.InlineKeyboardMarkup();kb.add(types.InlineKeyboardButton("Обміняти ×1",callback_data=PREFIX+"confirm"));kb.add(types.InlineKeyboardButton("🔙 Назад",callback_data=PREFIX+"home"));_edit(bot,call,"🛍 Крамниця\n\n3 × 🧪 Експериментальний жетон → 1 × 🎁 Пам’ятний знак випробування",kb);return
        if data=="confirm":
            if not _active():_edit(bot,call,"🛍 Крамниця\n\n⏳ Івент готується. Дати проведення буде оголошено пізніше.",_back());return
            kb=types.InlineKeyboardMarkup();kb.row(types.InlineKeyboardButton("✅ Підтвердити",callback_data=PREFIX+f"exchange:{call.message.message_id}"),types.InlineKeyboardButton("❌ Скасувати",callback_data=PREFIX+"shop"));_edit(bot,call,"Підтвердити один обмін 3 жетонів на 1 знак?",kb);return
        if data.startswith("exchange:"):
            if not _active():_edit(bot,call,"🛍 Крамниця\n\n⏳ Івент готується. Дати проведення буде оголошено пізніше.",_back());return
            from db_modules.connection import conn
            from systems.event_shop_system import exchange_event_shop_offer
            key=f"tg:event:test_event_2026:{call.from_user.id}:{data.split(':',1)[1]}"
            try:result=exchange_event_shop_offer(conn,"test_event_2026",call.from_user.id,"test_reward_exchange",key,event_active=True);conn.commit();text="✅ Обмін виконано." if result.get("success") else "❌ Обмін недоступний."
            except ValueError as error:conn.rollback();text="❌ Недостатньо вільних жетонів або місця в сумці." if str(error) in {"insufficient_unreserved_currency","bag_full"} else "❌ Обмін не виконано."
            _edit(bot,call,text,_back());return
        if data.startswith("rank:"):
            try:page=max(1,min(10,int(data.split(":",1)[1])))
            except Exception:page=1
            entries,own=_rank_rows(call.from_user.id,page);body="\n".join(entries) if entries else "Рейтинг поки порожній.";_edit(bot,call,f"🏆 Рейтинг івенту\nТоп-100, сторінка {page}/10\n\n{body}\n\n{own}",_rank_kb(page,len(entries)==10 and page<10));return
        _edit(bot,call,_main_text(),_main_kb())
