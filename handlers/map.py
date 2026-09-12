from __future__ import annotations
from datetime import datetime, timezone
from telebot import types
from data.locations import LOCATIONS, get_location, is_location_unlocked
from data.location_graph import CITY_NODE, TRAVEL_SECONDS, WORLD_NODES, get_adjacent_nodes
from data.mobs import get_mobs_for_location
from db import get_current_location, get_player_stats
from keyboards import map_kb, main_kb, city_kb
from systems.travel_system import get_active_travel, get_travel, start_travel, cancel_travel

MAP_COLLAPSE_BUTTON = "🔽 Згорнути мапу"

def get_player_level_from_stats(user_id):
    stats=get_player_stats(user_id)
    return int(stats[5] or 1) if stats else 1

def _node_name(node_id):
    return (WORLD_NODES.get(str(node_id)) or {}).get("name", str(node_id))

def _safe_answer(bot,call,text=None,alert=False):
    try: bot.answer_callback_query(call.id,text=text,show_alert=alert)
    except Exception: pass

def _remaining_seconds(travel,now=None):
    current=now or datetime.now(timezone.utc)
    arrival=datetime.fromisoformat(str(travel["arrival_at"]))
    if arrival.tzinfo is None: arrival=arrival.replace(tzinfo=timezone.utc)
    return max(0,int((arrival-current).total_seconds()+0.999))

def build_location_info_text(location_id,player_level):
    location=get_location(location_id); mobs=get_mobs_for_location(location_id)
    text=(f"{location['name']}\n\n🏷 Рівні зони: {location['level_min']}–{location['level_max']}\n\n📖 {location['description']}\n\n👹 Моби цієї зони:\n")
    for mob in mobs: text+=f"• {mob['name']}\n"
    if player_level>int(location['level_max']): text+="\n⚠️ Твій рівень перевищує рекомендований рівень цієї зони."
    return text.rstrip()

def build_world_map_text(user_id):
    active=get_active_travel(user_id)
    if active:
        return ("🚶 Триває подорож\n\n"+f"{_node_name(active['from_node'])}\n→ {_node_name(active['to_node'])}\n\n"+f"⏱️ Залишилося: {_remaining_seconds(active)} сек.\n\n"+"Поточне місцезнаходження зміниться лише після прибуття.")
    node=get_current_location(user_id) or CITY_NODE; level=get_player_level_from_stats(user_id)
    if node==CITY_NODE:
        return "🗺️ Мапа світу\n\n📍 Поточне місцезнаходження:\n🏙️ Місто\n\nДоступний напрямок:\n• 🌿 Початок Шляху"
    location=get_location(node)
    return ("🗺️ Мапа світу\n\n📍 Поточна локація:\n"+f"{location['name']}\n\n👤 Твій рівень: {level}\n\n📖 {location['description']}")

def build_map_inline_kb(user_id):
    kb=types.InlineKeyboardMarkup(row_width=1); active=get_active_travel(user_id)
    if active:
        kb.add(types.InlineKeyboardButton("❌ Скасувати подорож",callback_data=f"map:cancel:{active['id']}:{active['revision']}"));return kb
    current=get_current_location(user_id) or CITY_NODE; level=get_player_level_from_stats(user_id)
    for target in get_adjacent_nodes(current):
        node=WORLD_NODES[target]
        if target!=CITY_NODE and not is_location_unlocked(target,level):
            unlock=int(LOCATIONS[target]['unlock_level']); label=f"🔒 {node['name']} · {unlock} рівень"; data=f"map:locked:{target}"
        else:
            if target==CITY_NODE: label="🏙️ Повернутися у Місто"
            elif current==CITY_NODE: label=f"🚶 Вирушити у {node['name'].split(' ',1)[-1]}"
            elif target=='start_path': label="🌿 Повернутися у Початок Шляху"
            else: label=f"🚶 Вирушити у {node['name'].split(' ',1)[-1]}"
            data=f"map:preview:{target}"
        kb.add(types.InlineKeyboardButton(label,callback_data=data))
    if current!=CITY_NODE: kb.add(types.InlineKeyboardButton("👥 Гравці локації",callback_data="map:players"))
    return kb

def build_travel_preview_text(user_id,target):
    source=get_current_location(user_id) or CITY_NODE
    return ("🚶 Подорож\n\n"+f"Звідки: {_node_name(source)}\n"+f"Куди: {_node_name(target)}\n\n"+f"⏱️ Час у дорозі: {TRAVEL_SECONDS} секунд\n\n"+"Місцезнаходження зміниться тільки після завершення подорожі.")

def build_travel_preview_kb(target):
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🚶 Вирушити",callback_data=f"map:start:{target}"))
    kb.add(types.InlineKeyboardButton("◀️ Повернутися до мапи",callback_data="map:open"));return kb

def render_map_message(bot,chat_id,user_id,message_id=None):
    text=build_world_map_text(user_id); inline=build_map_inline_kb(user_id)
    if message_id is not None:
        try: bot.edit_message_text(text,chat_id=chat_id,message_id=message_id,reply_markup=inline);return
        except Exception: pass
    bot.send_message(chat_id,text,reply_markup=inline)

def _failure_message(reason):
    return {"location_locked":"🔒 Локація ще недоступна за рівнем.","not_adjacent":"⚠️ Цей напрямок більше не є сусіднім.","already_travelling":"🚶 Подорож уже триває.","unknown_destination":"⚠️ Невідомий напрямок.","invalid_current_node":"⚠️ Поточне місцезнаходження некоректне.","player_busy":"⚠️ Зараз персонаж зайнятий іншою дією."}.get(reason,"⚠️ Не вдалося розпочати подорож. Відкрий мапу повторно.")

def register_map_handlers(bot):
    @bot.message_handler(func=lambda m:m.text in ("🗺️ Мапа","🔙 Мапа"))
    def show_map(message):
        bot.send_message(message.chat.id,"🗺️ Мапу відкрито.",reply_markup=map_kb());render_map_message(bot,message.chat.id,message.from_user.id)

    @bot.message_handler(func=lambda m:m.text==MAP_COLLAPSE_BUTTON)
    def collapse_map(message):
        node=get_current_location(message.from_user.id) or CITY_NODE
        kb=city_kb() if node==CITY_NODE else main_kb()
        text="🔽 Мапу згорнуто."
        bot.send_message(message.chat.id,text,reply_markup=kb)

    @bot.callback_query_handler(func=lambda c:str(getattr(c,'data','')).startswith('map:'))
    def map_callbacks(call):
        data=str(call.data);parts=data.split(':');action=parts[1] if len(parts)>1 else ''
        uid=int(call.from_user.id);chat=call.message.chat.id;mid=call.message.message_id
        if action=='open': _safe_answer(bot,call);render_map_message(bot,chat,uid,mid);return
        if action=='players':
            _safe_answer(bot,call)
            if get_active_travel(uid): _safe_answer(bot,call,"Під час подорожі список недоступний.",True);return
            from systems.player_interaction_system import get_online_players_in_same_location,touch_player_activity
            from handlers.player_interaction import build_location_players_text,build_location_players_kb
            touch_player_activity(uid);result=get_online_players_in_same_location(uid,page=0,page_size=8)
            bot.edit_message_text(build_location_players_text(result),chat_id=chat,message_id=mid,parse_mode='HTML',reply_markup=build_location_players_kb(result));return
        if action=='locked':
            target=parts[2] if len(parts)>2 else '';loc=LOCATIONS.get(target) or {};_safe_answer(bot,call,f"Потрібний рівень: {loc.get('unlock_level','?')}",True);return
        if action=='preview':
            _safe_answer(bot,call);target=parts[2] if len(parts)>2 else ''
            # Authoritative validation occurs again in start_travel.
            if target not in get_adjacent_nodes(get_current_location(uid) or CITY_NODE): render_map_message(bot,chat,uid,mid);return
            bot.edit_message_text(build_travel_preview_text(uid,target),chat_id=chat,message_id=mid,reply_markup=build_travel_preview_kb(target));return
        if action=='start':
            target=parts[2] if len(parts)>2 else '';result=start_travel(uid,target)
            if not result.get('success'): _safe_answer(bot,call,_failure_message(result.get('reason')),True);render_map_message(bot,chat,uid,mid);return
            _safe_answer(bot,call,"Подорож розпочато");render_map_message(bot,chat,uid,mid);return
        if action=='cancel':
            try: travel_id=int(parts[2]);revision=int(parts[3])
            except Exception: _safe_answer(bot,call,"Некоректна дія.",True);return
            result=cancel_travel(uid,travel_id,expected_revision=revision)
            _safe_answer(bot,call,"Подорож скасовано." if result.get('success') else "Подорож уже завершена.",not result.get('success'))
            render_map_message(bot,chat,uid,mid);return
        _safe_answer(bot,call,"Дія неактуальна.",True)
