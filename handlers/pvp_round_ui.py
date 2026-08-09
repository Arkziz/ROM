from __future__ import annotations

import logging
from telebot import types

from systems.player_interaction_system import release_player_activity_session
from systems.pvp_combat_log import render_pvp_round_combat_log
from systems.pvp_action_validation import validate_pvp_action_choice
from systems.pvp_round_ui import build_pvp_action_keyboard, render_pvp_round_text
from systems.pvp_system import (
    cleanup_terminal_pvp_activity_sessions,
    get_active_pvp_battle_for_user,
    get_pvp_battle,
    get_pvp_participants,
    get_pvp_round_actions,
    list_active_pvp_battles,
    resolve_persisted_pvp_round,
    submit_pvp_action,
)
from systems.pvp_completion_service import cleanup_all_terminal_pvp_sessions, render_pvp_terminal_text, surrender_pvp_battle
from systems.pvp_timer_service import start_pvp_timer_worker

log=logging.getLogger(__name__)
_registered=False
PVP_STATUS_BUTTON="⚔️ Стан дуелі"


def pvp_active_reply_kb():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=1)
    kb.add(types.KeyboardButton(PVP_STATUS_BUTTON))
    return kb


def _main_kb():
    try:
        from keyboards import main_kb
        return main_kb()
    except Exception:
        return types.ReplyKeyboardRemove()


def _pair(battle_id,user_id):
    rows=get_pvp_participants(int(battle_id))
    own=next((x for x in rows if int(x["user_id"])==int(user_id)),None)
    enemy=next((x for x in rows if int(x["user_id"])!=int(user_id)),None)
    return own,enemy


def _has_action(battle,user_id):
    return any(int(x["user_id"])==int(user_id) for x in get_pvp_round_actions(int(battle["id"]),int(battle["round_number"]),int(battle["revision"])))


def _pvp_terminal(battle):
    return bool(battle) and str(battle.get("status") or "") in {"completed","cancelled","expired"}


def _terminal_callback_answer(bot, call):
    bot.answer_callback_query(call.id,"ℹ️ Дуель уже завершена. Старі бойові кнопки більше не активні.",show_alert=True)


def _localized_pvp_action_error(error):
    key=str(error or "").strip().lower()
    return {
        "pvp battle is not active":"ℹ️ Дуель уже завершена. Старі бойові кнопки більше не активні.",
        "battle is not active":"ℹ️ Дуель уже завершена. Старі бойові кнопки більше не активні.",
        "stale pvp round callback":"ℹ️ Цей раунд уже завершено. Відкрийте актуальний стан дуелі.",
        "actor is not a pvp participant":"❌ Ця дуель належить іншим гравцям.",
        "pvp action already submitted":"ℹ️ Дію для цього раунду вже обрано.",
        "unsupported pvp action type":"❌ Невідома бойова дія.",
    }.get(key,"❌ Не вдалося виконати бойову дію. Оновіть стан дуелі.")


def _release_terminal_participants(battle_id):
    for row in get_pvp_participants(int(battle_id)):
        release_player_activity_session(
            int(row["user_id"]),
            activity_type="pvp_battle",
            reference_id=int(battle_id),
        )


def send_pvp_round_panel(bot,battle_id,user_id):
    battle=get_pvp_battle(int(battle_id))
    if not battle: return
    own,enemy=_pair(battle_id,user_id)
    if not own or not enemy: return
    waiting=_has_action(battle,user_id) if battle.get("status")=="active" else False
    if battle.get("status") in {"completed","cancelled","expired"}:
        bot.send_message(int(user_id),render_pvp_terminal_text(int(battle_id),int(user_id)),parse_mode="HTML",reply_markup=_main_kb())
        return
    bot.send_message(
        int(user_id),
        render_pvp_round_text(battle,own,enemy,waiting),
        parse_mode="HTML",
        reply_markup=build_pvp_action_keyboard(battle,own,action_submitted=waiting),
    )


def broadcast_pvp_round_log(bot, battle_id, payload):
    if not payload:
        return
    for row in get_pvp_participants(int(battle_id)):
        try:
            bot.send_message(
                int(row["user_id"]),
                render_pvp_round_combat_log(payload, int(row["user_id"])),
                parse_mode="HTML",
            )
        except Exception:
            log.exception("Cannot send PvP round combat log")


def broadcast_pvp_state(bot,battle_id):
    battle=get_pvp_battle(int(battle_id))
    participants=get_pvp_participants(int(battle_id))
    for row in participants:
        try: send_pvp_round_panel(bot,battle_id,int(row["user_id"]))
        except Exception: log.exception("Cannot send PvP panel")
    if battle and battle.get("status") in {"completed","cancelled","expired"}:
        _release_terminal_participants(int(battle_id))


def activate_pvp_battle_ui(bot,battle_id):
    """Replace the normal persistent menu and immediately open the current round."""
    for row in get_pvp_participants(int(battle_id)):
        uid=int(row["user_id"])
        bot.send_message(uid,"⚔️ Режим дуелі активовано.",reply_markup=pvp_active_reply_kb())
    broadcast_pvp_state(bot,int(battle_id))


def register_pvp_round_ui_handlers(bot):
    global _registered
    if _registered: return
    _registered=True

    @bot.message_handler(func=lambda message: getattr(message,"text",None)==PVP_STATUS_BUTTON)
    def pvp_status_message(message):
        battle=get_active_pvp_battle_for_user(int(message.from_user.id))
        if not battle:
            bot.send_message(message.chat.id,"ℹ️ Активної дуелі немає.",reply_markup=_main_kb())
            return
        send_pvp_round_panel(bot,int(battle["id"]),int(message.from_user.id))

    @bot.callback_query_handler(func=lambda call: str(getattr(call,"data","")).startswith("pvp:round:"))
    def pvp_round_callback(call):
        parts=str(call.data).split(":")
        if len(parts)<7: return
        mode=parts[2]
        try: bid,rnd,rev=int(parts[3]),int(parts[4]),int(parts[5])
        except (TypeError,ValueError): return
        battle=get_pvp_battle(bid)
        if _pvp_terminal(battle):
            _terminal_callback_answer(bot,call); return
        if not battle or int(battle.get("round_number") or 0)!=rnd or int(battle.get("revision") or 0)!=rev:
            bot.answer_callback_query(call.id,"Цей раунд уже завершено. Оновіть стан дуелі.",show_alert=True); return
        own,enemy=_pair(bid,int(call.from_user.id))
        if not own:
            bot.answer_callback_query(call.id,"Ця дуель належить іншим гравцям.",show_alert=True); return
        if mode=="refresh":
            bot.answer_callback_query(call.id); send_pvp_round_panel(bot,bid,int(call.from_user.id)); return
        if mode!="act": return
        action=parts[6]; skill=parts[7] if action=="skill" and len(parts)>7 else None
        validation=validate_pvp_action_choice(own,action,skill)
        if not validation.get("success"):
            # Do not persist an invalid intent and do not reset the existing deadline.
            bot.answer_callback_query(call.id,str(validation.get("message") or "Оберіть іншу дію."),show_alert=True)
            return
        try:
            result=submit_pvp_action(bid,int(call.from_user.id),rnd,rev,action,skill_key=skill)
        except ValueError as exc:
            bot.answer_callback_query(call.id,_localized_pvp_action_error(exc),show_alert=True); return
        bot.answer_callback_query(call.id,"Дію прийнято")
        if result.get("both_ready"):
            resolved=resolve_persisted_pvp_round(bid,rnd,rev,seed=(bid*100000+rnd))
            if resolved.get("resolved"):
                broadcast_pvp_round_log(bot, bid, resolved.get("round_payload"))
                broadcast_pvp_state(bot,bid)
        else:
            send_pvp_round_panel(bot,bid,int(call.from_user.id))

    @bot.callback_query_handler(func=lambda call: str(getattr(call,"data","")).startswith("pvp:surrender:"))
    def pvp_surrender_callback(call):
        parts=str(call.data).split(":")
        if len(parts)!=5: return
        mode=parts[2]
        try: battle_id,revision=int(parts[3]),int(parts[4])
        except (TypeError,ValueError): return
        battle=get_pvp_battle(battle_id)
        if _pvp_terminal(battle):
            _terminal_callback_answer(bot,call); return
        if not battle or int(battle.get("revision") or 0)!=revision:
            bot.answer_callback_query(call.id,"Ця панель уже застаріла. Відкрийте актуальний стан дуелі.",show_alert=True); return
        own,enemy=_pair(battle_id,int(call.from_user.id))
        if not own or not enemy:
            bot.answer_callback_query(call.id,"Ця дуель належить іншим гравцям.",show_alert=True); return
        if mode=="ask":
            kb=types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("🏳️ Так, здатися",callback_data=f"pvp:surrender:confirm:{battle_id}:{revision}"))
            kb.add(types.InlineKeyboardButton("↩️ Продовжити дуель",callback_data=f"pvp:surrender:cancel:{battle_id}:{revision}"))
            bot.answer_callback_query(call.id)
            bot.send_message(int(call.from_user.id),"🏳️ <b>Підтвердіть, що ви бажаєте здатися.</b>\n\nПісля підтвердження суперник буде оголошений переможцем, а дуель завершиться.",parse_mode="HTML",reply_markup=kb); return
        if mode=="cancel":
            bot.answer_callback_query(call.id,"Дуель продовжується."); send_pvp_round_panel(bot,battle_id,int(call.from_user.id)); return
        if mode!="confirm": return
        result=surrender_pvp_battle(battle_id,int(call.from_user.id),revision)
        if not result.get("success"):
            text={"battle_already_finished":"Дуель уже завершена.","stale_revision":"Ця панель вже застаріла.","wrong_actor":"Ця дуель належить іншим гравцям."}.get(result.get("reason"),"Не вдалося завершити дуель.")
            bot.answer_callback_query(call.id,text,show_alert=True); return
        bot.answer_callback_query(call.id,"Дуель завершено.")
        for row in get_pvp_participants(battle_id):
            uid=int(row["user_id"])
            try: bot.send_message(uid,render_pvp_terminal_text(battle_id,uid),parse_mode="HTML",reply_markup=_main_kb())
            except Exception: log.exception("Cannot send PvP surrender result")

    cleanup_all_terminal_pvp_sessions()
    def _timer_broadcast(battle_id, result=None):
        if result:
            broadcast_pvp_round_log(bot, battle_id, result.get("round_payload"))
        broadcast_pvp_state(bot, battle_id)
    start_pvp_timer_worker(_timer_broadcast)
    for battle in list_active_pvp_battles():
        try: activate_pvp_battle_ui(bot,int(battle["id"]))
        except Exception: log.exception("Cannot restore PvP battle UI")
