from __future__ import annotations

import logging
from telebot import types

from systems.pvp_round_ui import build_pvp_action_keyboard, render_pvp_round_text
from systems.pvp_system import get_pvp_battle, get_pvp_participants, get_pvp_round_actions, list_active_pvp_battles, resolve_persisted_pvp_round, submit_pvp_action
from systems.pvp_timer_service import start_pvp_timer_worker

log=logging.getLogger(__name__)
_registered=False

def _pair(battle_id,user_id):
    rows=get_pvp_participants(int(battle_id))
    own=next((x for x in rows if int(x["user_id"])==int(user_id)),None)
    enemy=next((x for x in rows if int(x["user_id"])!=int(user_id)),None)
    return own,enemy

def _has_action(battle,user_id):
    return any(int(x["user_id"])==int(user_id) for x in get_pvp_round_actions(int(battle["id"]),int(battle["round_number"]),int(battle["revision"])))

def send_pvp_round_panel(bot,battle_id,user_id):
    battle=get_pvp_battle(int(battle_id))
    if not battle: return
    own,enemy=_pair(battle_id,user_id)
    if not own or not enemy: return
    waiting=_has_action(battle,user_id) if battle.get("status")=="active" else False
    if battle.get("status") in {"completed","cancelled","expired"}:
        winner=battle.get("winner_id")
        text="🤝 <b>Дуель завершено нічиєю.</b>" if winner is None else ("🏆 <b>Ви перемогли в дуелі!</b>" if int(winner)==int(user_id) else "💀 <b>Ви програли дуель.</b>")
        bot.send_message(int(user_id),text,parse_mode="HTML")
        return
    bot.send_message(int(user_id),render_pvp_round_text(battle,own,enemy,waiting),parse_mode="HTML",reply_markup=build_pvp_action_keyboard(battle,own,action_submitted=waiting))

def broadcast_pvp_state(bot,battle_id):
    for row in get_pvp_participants(int(battle_id)):
        try: send_pvp_round_panel(bot,battle_id,int(row["user_id"]))
        except Exception: log.exception("Cannot send PvP panel")

def register_pvp_round_ui_handlers(bot):
    global _registered
    if _registered: return
    _registered=True

    @bot.callback_query_handler(func=lambda call: str(getattr(call,"data","")).startswith("pvp:round:"))
    def pvp_round_callback(call):
        parts=str(call.data).split(":")
        if len(parts)<7: return
        mode=parts[2]
        try: bid,rnd,rev=int(parts[3]),int(parts[4]),int(parts[5])
        except (TypeError,ValueError): return
        battle=get_pvp_battle(bid)
        if not battle or int(battle.get("round_number") or 0)!=rnd or int(battle.get("revision") or 0)!=rev:
            bot.answer_callback_query(call.id,"Цей раунд уже завершено. Оновіть стан дуелі.",show_alert=True); return
        own,enemy=_pair(bid,int(call.from_user.id))
        if not own:
            bot.answer_callback_query(call.id,"Ця дуель належить іншим гравцям.",show_alert=True); return
        if mode=="refresh":
            bot.answer_callback_query(call.id)
            send_pvp_round_panel(bot,bid,int(call.from_user.id)); return
        if mode!="act": return
        action=parts[6]; skill=parts[7] if action=="skill" and len(parts)>7 else None
        try:
            result=submit_pvp_action(bid,int(call.from_user.id),rnd,rev,action,skill_key=skill)
        except ValueError as exc:
            bot.answer_callback_query(call.id,str(exc),show_alert=True); return
        bot.answer_callback_query(call.id,"Дію прийнято")
        if result.get("both_ready"):
            resolved=resolve_persisted_pvp_round(bid,rnd,rev,seed=(bid*100000+rnd))
            if resolved.get("resolved"): broadcast_pvp_state(bot,bid)
        else:
            send_pvp_round_panel(bot,bid,int(call.from_user.id))

    start_pvp_timer_worker(lambda battle_id: broadcast_pvp_state(bot,battle_id))
    # Restore active battles, including battles created before Stage 14.4.
    for battle in list_active_pvp_battles():
        try: broadcast_pvp_state(bot,int(battle["id"]))
        except Exception: log.exception("Cannot restore PvP battle UI")
