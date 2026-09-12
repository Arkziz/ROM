from __future__ import annotations

from telebot import types

from systems.pvp_battle_factory import create_pvp_battle_from_accepted_duel, prepare_pvp_duel_snapshots
from systems.pvp_request_service import create_pvp_duel_request, respond_to_pvp_duel_request, cancel_failed_accepted_pvp_duel_request
from systems.player_interaction_system import get_interaction_request


def _answer(bot, call, text=None, alert=False):
    try:
        bot.answer_callback_query(call.id, text=text, show_alert=alert)
    except Exception:
        pass


def _edit(bot, call, text, reply_markup=None):
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=reply_markup)
    except Exception as exc:
        if "message is not modified" not in str(exc).lower():
            raise


def _pve_busy(user_id):
    try:
        from handlers.player_interaction import _possible_pve_busy
        return bool(_possible_pve_busy(int(user_id)))
    except Exception:
        return False


def _failure(reason):
    return {
        "self_target": "❌ Не можна викликати на дуель власного персонажа.",
        "player_not_found": "❌ Гравець більше недоступний.",
        "player_offline": "❌ Один із гравців більше не перебуває онлайн.",
        "different_location": "❌ Гравці вже не перебувають в одній локації.",
        "player_busy": "❌ Один із гравців уже зайнятий боєм, обміном або іншим запитом.",
        "player_in_battle": "❌ Дуель неможлива, поки один із гравців перебуває у PvE-бою.",
        "request_expired": "⌛ Виклик на дуель уже прострочений.",
        "stale_revision": "⌛ Цей виклик уже неактуальний.",
        "wrong_actor": "❌ Цей виклик призначений іншому гравцеві.",
        "request_not_pending": "ℹ️ Виклик уже було оброблено.",
        "pvp_snapshot_failed": "❌ Не вдалося підготувати характеристики персонажів для PvP.",
        "pvp_battle_creation_failed": "❌ Не вдалося створити PvP-бій.",
    }.get(reason, "❌ Не вдалося виконати дію з викликом на дуель.")


def register_pvp_interaction_handlers(bot):
    """Register before the Stage 12 base registrar so the old duel placeholder cannot intercept."""
    from handlers.pvp_round_ui import register_pvp_round_ui_handlers
    register_pvp_round_ui_handlers(bot)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:duel:"))
    def pvp_duel_request(call):
        from systems.travel_system import is_user_travelling
        if is_user_travelling(int(call.from_user.id)):
            _answer(bot,call,'Дуель недоступна під час подорожі.',True);return
        _answer(bot, call)
        try:
            target_id = int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError):
            return
        result = create_pvp_duel_request(int(call.from_user.id), target_id, pve_busy_checker=_pve_busy)
        if not result.get("success"):
            bot.send_message(call.message.chat.id, _failure(result.get("reason")))
            return
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.row(
            types.InlineKeyboardButton("✅ Прийняти дуель", callback_data=f"pvp:req:accept:{result['request_id']}:1"),
            types.InlineKeyboardButton("❌ Відхилити", callback_data=f"pvp:req:decline:{result['request_id']}:1"),
        )
        bot.send_message(
            target_id,
            "⚔️ <b>Виклик на дуель</b>\n\n"
            f"Гравець {result['initiator_name']} викликає вас на дуель.\n\n"
            "Дуель не змінює реальні HP, MP, міцність, предмети, золото або досвід.\n"
            "Запрошення діє 2 хвилини.",
            parse_mode="HTML", reply_markup=kb,
        )
        bot.send_message(
            call.message.chat.id,
            "✅ <b>Виклик на дуель відправлено</b>\n\n"
            f"Гравець: {result['recipient_name']}\nОчікуємо відповідь протягом 2 хвилин.",
            parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith(("pvp:req:accept:", "pvp:req:decline:")))
    def pvp_duel_response(call):
        from systems.travel_system import is_user_travelling
        if is_user_travelling(int(call.from_user.id)):
            _answer(bot,call,'Дуель недоступна під час подорожі.',True);return
        parts = str(call.data).split(":")
        if len(parts) != 5:
            return
        action = parts[2]
        try:
            request_id, revision = int(parts[3]), int(parts[4])
        except (TypeError, ValueError):
            return
        prepared = None
        if action == "accept":
            pending = get_interaction_request(request_id)
            if not pending or pending.get("request_type") != "duel":
                _answer(bot, call, _failure("request_not_found"), True)
                return
            prepared = prepare_pvp_duel_snapshots(
                int(pending["initiator_user_id"]), int(pending["recipient_user_id"])
            )
            if not prepared.get("success"):
                _answer(bot, call, _failure(prepared.get("reason")), True)
                return
        result = respond_to_pvp_duel_request(
            request_id, int(call.from_user.id), action,
            expected_revision=revision, pve_busy_checker=_pve_busy,
        )
        if not result.get("success"):
            _answer(bot, call, _failure(result.get("reason")), True)
            return
        if result.get("status") == "declined":
            _answer(bot, call)
            _edit(bot, call, "❌ Виклик на дуель відхилено.")
            try:
                bot.send_message(int(result["initiator_user_id"]), "❌ Виклик на дуель відхилено.")
            except Exception:
                pass
            return
        battle = create_pvp_battle_from_accepted_duel(result, prepared_snapshots=prepared)
        if not battle.get("success"):
            cancel_failed_accepted_pvp_duel_request(request_id)
            technical = str(battle.get("error") or battle.get("reason") or "unknown")[:180]
            _answer(bot, call, _failure(battle.get("reason")), True)
            bot.send_message(
                call.message.chat.id,
                "❌ PvP-бій не створено. Виклик безпечно скасовано, можна надіслати новий.\n"
                f"Технічна причина: {technical}",
            )
            return
        battle_id = int(battle["battle_id"])
        text = (
            "✅ <b>Дуель прийнято</b>\n\n"
            f"PvP-бій #{battle_id} створено.\n"
            "Обидва персонажі зарезервовані для дуелі.\n\n"
            "⚔️ Перший раунд відкривається окремим повідомленням."
        )
        _answer(bot, call)
        _edit(bot, call, text)
        try:
            bot.send_message(int(result["initiator_user_id"]), text, parse_mode="HTML")
        except Exception:
            pass
        from handlers.pvp_round_ui import activate_pvp_battle_ui
        activate_pvp_battle_ui(bot, battle_id)
