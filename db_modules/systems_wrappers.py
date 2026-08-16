"""
System wrappers module - delegating to systems/* modules

This module contains wrapper functions for:
- Energy system (systems.energy_system)
- Regeneration system (systems.regen_system)
- Guild system (systems.guild_system)
- Auction house (systems.auction_house_system)
- Rune system (systems.rune_system)
- Contract system (systems.contract_system)
- Player interaction (systems.player_interaction_system)
"""


# ==============================
# ENERGY SYSTEM
# ==============================

def _energy_system():
    from systems import energy_system
    return energy_system


def init_energy_system():
    return _energy_system().init_energy_system()


def get_user_energy(user_id):
    return _energy_system().get_user_energy(user_id)


def consume_energy_for_hunt(user_id):
    return _energy_system().consume_energy_for_hunt(user_id)


def restore_energy_for_test(user_id, amount=40):
    return _energy_system().restore_energy_for_test(user_id, amount=amount)


def get_users_for_energy_full_notification():
    return _energy_system().get_users_for_energy_full_notification()

def reset_daily_hunts_if_needed(user_id):
    return _energy_system().reset_daily_hunts_if_needed(user_id)

# ==============================
# REGENERATION SYSTEM
# ==============================

def _regen_system():
    from systems import regen_system
    return regen_system


def init_hp_regen_system():
    return _regen_system().init_hp_regen_system()


def init_passive_regen_system():
    return _regen_system().init_passive_regen_system()


def process_passive_regeneration(user_id):
    return _regen_system().process_passive_regeneration(user_id)


def reset_hp_regen_timers_now(user_id):
    return _regen_system().reset_hp_regen_timers_now(user_id)


def apply_passive_hp_regen(user_id):
    return _regen_system().apply_passive_hp_regen(user_id)


# ==============================
# GUILD SYSTEM
# ==============================

def _guild_system():
    from systems import guild_system
    return guild_system


def init_guild_system():
    return _guild_system().init_guild_system()


def get_current_guild_season_key():
    return _guild_system().get_current_guild_season_key()


def ensure_all_guild_monthly_seasons():
    return _guild_system().ensure_all_guild_monthly_seasons()


def ensure_guild_monthly_season(guild_id):
    return _guild_system().ensure_guild_monthly_season(guild_id)


def create_guild(user_id, name, tag, icon="🏰"):
    return _guild_system().create_guild(user_id=user_id, name=name, tag=tag, icon=icon)


def get_user_guild(user_id):
    return _guild_system().get_user_guild(user_id)


def get_user_guild_member(user_id):
    return _guild_system().get_user_guild_member(user_id)


def get_user_guild_role(user_id):
    return _guild_system().get_user_guild_role(user_id)


def is_user_in_guild(user_id):
    return _guild_system().is_user_in_guild(user_id)


def get_guild_by_id(guild_id):
    return _guild_system().get_guild_by_id(guild_id)


def get_guild_by_name_or_tag(value):
    return _guild_system().get_guild_by_name_or_tag(value)


def get_guild_members(guild_id):
    return _guild_system().get_guild_members(guild_id)


def get_guild_member_count(guild_id):
    return _guild_system().get_guild_member_count(guild_id)


def create_guild_application(user_id, guild_id):
    return _guild_system().create_guild_application(user_id=user_id, guild_id=guild_id)


def get_guild_applications(guild_id, status="pending"):
    return _guild_system().get_guild_applications(guild_id=guild_id, status=status)


def can_manage_guild_applications(user_id, guild_id):
    return _guild_system().can_manage_guild_applications(user_id=user_id, guild_id=guild_id)


def add_guild_progress(guild_id, exp=0, resource=0, kills=0, contracts=0, user_id=None, reason=""):
    return _guild_system().add_guild_progress(
        guild_id=guild_id, exp=exp, resource=resource, kills=kills,
        contracts=contracts, user_id=user_id, reason=reason
    )


def get_guild_ranking(scope="monthly", limit=10):
    return _guild_system().get_guild_ranking(scope=scope, limit=limit)


def get_guild_season_history(guild_id=None, season_key=None, limit=20):
    return _guild_system().get_guild_season_history(
        guild_id=guild_id, season_key=season_key, limit=limit
    )


def get_guild_display_name(guild):
    return _guild_system().get_guild_display_name(guild)


def get_guild_role_label(role):
    return _guild_system().get_guild_role_label(role)


def get_user_guild_profile_line(user_id):
    return _guild_system().get_user_guild_profile_line(user_id)


def get_public_guild_list(limit=50, offset=0):
    return _guild_system().get_public_guild_list(limit=limit, offset=offset)


def get_user_guild_applications(user_id, status=None):
    return _guild_system().get_user_guild_applications(user_id=user_id, status=status)


def has_pending_guild_application(user_id, guild_id):
    return _guild_system().has_pending_guild_application(user_id=user_id, guild_id=guild_id)


def cancel_guild_application(user_id, application_id):
    return _guild_system().cancel_guild_application(user_id=user_id, application_id=application_id)


def get_guild_by_icon(icon):
    return _guild_system().get_guild_by_icon(icon)


def is_guild_icon_taken(icon, exclude_guild_id=None):
    return _guild_system().is_guild_icon_taken(icon=icon, exclude_guild_id=exclude_guild_id)


def make_existing_guild_icons_unique():
    return _guild_system().make_existing_guild_icons_unique()


def ensure_unique_guild_icon_index():
    return _guild_system().ensure_unique_guild_icon_index()


def get_guild_application_by_id(application_id):
    return _guild_system().get_guild_application_by_id(application_id)


def accept_guild_application(actor_user_id, application_id):
    return _guild_system().accept_guild_application(actor_user_id=actor_user_id, application_id=application_id)


def reject_guild_application(actor_user_id, application_id):
    return _guild_system().reject_guild_application(actor_user_id=actor_user_id, application_id=application_id)


def get_guild_member(guild_id, user_id):
    return _guild_system().get_guild_member(guild_id=guild_id, user_id=user_id)


def get_character_name_by_user_id(user_id):
    return _guild_system().get_character_name_by_user_id(user_id)


def is_guild_leader(user_id, guild_id):
    return _guild_system().is_guild_leader(user_id=user_id, guild_id=guild_id)


def is_guild_officer(user_id, guild_id):
    return _guild_system().is_guild_officer(user_id=user_id, guild_id=guild_id)


def promote_guild_member_to_officer(actor_user_id, target_user_id):
    return _guild_system().promote_guild_member_to_officer(
        actor_user_id=actor_user_id, target_user_id=target_user_id
    )


def demote_guild_officer(actor_user_id, target_user_id):
    return _guild_system().demote_guild_officer(actor_user_id=actor_user_id, target_user_id=target_user_id)


def kick_guild_member(actor_user_id, target_user_id):
    return _guild_system().kick_guild_member(actor_user_id=actor_user_id, target_user_id=target_user_id)


def get_guild_officer_count(guild_id):
    return _guild_system().get_guild_officer_count(guild_id)


def get_guild_officer_member(guild_id):
    return _guild_system().get_guild_officer_member(guild_id)


def cleanup_stale_guild_applications():
    return _guild_system().cleanup_stale_guild_applications()


def get_guild_exp_required_for_level(level):
    return _guild_system().get_guild_exp_required_for_level(level)


def calculate_guild_level_from_exp(total_exp):
    return _guild_system().calculate_guild_level_from_exp(total_exp)


def get_guild_next_level_info(guild_id):
    return _guild_system().get_guild_next_level_info(guild_id)


def recalculate_guild_level(guild_id):
    return _guild_system().recalculate_guild_level(guild_id)


def add_user_guild_progress(user_id, exp=0, resource=0, kills=0, contracts=0, reason=""):
    return _guild_system().add_user_guild_progress(
        user_id=user_id, exp=exp, resource=resource, kills=kills,
        contracts=contracts, reason=reason
    )


def get_guild_contribution_ranking(guild_id, scope="monthly", limit=30):
    return _guild_system().get_guild_contribution_ranking(
        guild_id=guild_id, scope=scope, limit=limit
    )


def cleanup_recalculate_all_guild_levels():
    return _guild_system().cleanup_recalculate_all_guild_levels()


def get_guild_logs(guild_id, limit=20, offset=0):
    return _guild_system().get_guild_logs(guild_id=guild_id, limit=limit, offset=offset)


def get_guild_logs_count(guild_id):
    return _guild_system().get_guild_logs_count(guild_id=guild_id)


def award_guild_elite_kill(user_id, mob=None):
    return _guild_system().award_guild_elite_kill(user_id=user_id, mob=mob)


def award_guild_contract_completion(user_id, contract=None):
    return _guild_system().award_guild_contract_completion(user_id=user_id, contract=contract)


def get_guild_activity_reward_text(result):
    return _guild_system().get_guild_activity_reward_text(result)


def get_guild_pending_applications_count(guild_id):
    return _guild_system().get_guild_pending_applications_count(guild_id)


def get_user_pending_applications_count(user_id):
    return _guild_system().get_user_pending_applications_count(user_id)


def get_guild_diagnostics(user_id):
    return _guild_system().get_guild_diagnostics(user_id)


def run_guild_sanity_cleanup():
    return _guild_system().run_guild_sanity_cleanup()


# ==============================
# AUCTION HOUSE SYSTEM
# ==============================

def _auction_system():
    from systems import auction_house_system
    return auction_house_system


def init_auction_house():
    return _auction_system().init_auction_house()


def validate_auction_price(value):
    return _auction_system().validate_auction_price(value)


def decimal_to_price_text(value):
    return _auction_system().decimal_to_price_text(value)


def auction_price_to_decimal(value):
    return _auction_system().auction_price_to_decimal(value)


def normalize_auction_category(category):
    return _auction_system().normalize_auction_category(category)


def add_auction_history(**kwargs):
    return _auction_system().add_auction_history(**kwargs)


def get_auction_lot_by_id(lot_id):
    return _auction_system().get_auction_lot_by_id(lot_id)


def get_user_active_auction_count(user_id):
    return _auction_system().get_user_active_auction_count(user_id)


def can_user_create_auction_lot(user_id):
    return _auction_system().can_user_create_auction_lot(user_id)


def get_auction_lots(status="ACTIVE", category=None, search_text=None, limit=10, offset=0, sort="new"):
    return _auction_system().get_auction_lots(
        status=status, category=category, search_text=search_text,
        limit=limit, offset=offset, sort=sort
    )


def create_auction_lot_record(**kwargs):
    return _auction_system().create_auction_lot_record(**kwargs)


def mark_auction_lot_status(lot_id, status_after, actor_user_id=None, event_type=None, details=None):
    return _auction_system().mark_auction_lot_status(
        lot_id, status_after, actor_user_id=actor_user_id,
        event_type=event_type, details=details
    )


def get_auction_house_stats():
    return _auction_system().get_auction_house_stats()


def get_user_sellable_equipment_for_auction(user_id, limit=50, offset=0):
    return _auction_system().get_user_sellable_equipment_for_auction(
        user_id=user_id, limit=limit, offset=offset
    )


def get_inventory_item_snapshot_for_auction(user_id, inventory_id):
    return _auction_system().get_inventory_item_snapshot_for_auction(
        user_id=user_id, inventory_id=inventory_id
    )


def validate_inventory_item_for_auction_equipment(user_id, inventory_id):
    return _auction_system().validate_inventory_item_for_auction_equipment(
        user_id=user_id, inventory_id=inventory_id
    )


def create_equipment_auction_lot(user_id, inventory_id, price):
    return _auction_system().create_equipment_auction_lot(
        user_id=user_id, inventory_id=inventory_id, price=price
    )


def get_user_sellable_stack_items_for_auction(user_id, category, limit=50, offset=0):
    return _auction_system().get_user_sellable_stack_items_for_auction(
        user_id=user_id, category=category, limit=limit, offset=offset
    )


def validate_inventory_stack_item_for_auction(user_id, inventory_id, category, quantity):
    return _auction_system().validate_inventory_stack_item_for_auction(
        user_id=user_id, inventory_id=inventory_id, category=category, quantity=quantity
    )


def create_stack_auction_lot(user_id, inventory_id, category, quantity, price):
    return _auction_system().create_stack_auction_lot(
        user_id=user_id, inventory_id=inventory_id, category=category,
        quantity=quantity, price=price
    )


def get_public_auction_lots_for_buyer(user_id, category=None, search_text=None, limit=8, offset=0, sort="new"):
    return _auction_system().get_public_auction_lots_for_buyer(
        user_id=user_id, category=category, search_text=search_text,
        limit=limit, offset=offset, sort=sort
    )


def build_auction_lot_public_details(lot_id, viewer_user_id=None):
    return _auction_system().build_auction_lot_public_details(
        lot_id=lot_id, viewer_user_id=viewer_user_id
    )


def buy_auction_lot(buyer_user_id, lot_id):
    return _auction_system().buy_auction_lot(buyer_user_id=buyer_user_id, lot_id=lot_id)


def build_auction_sell_item_review_text(user_id, inventory_id, category):
    return _auction_system().build_auction_sell_item_review_text(
        user_id=user_id, inventory_id=inventory_id, category=category
    )


def get_user_auction_lots(user_id, status=None, limit=8, offset=0):
    return _auction_system().get_user_auction_lots(
        user_id=user_id, status=status, limit=limit, offset=offset
    )


def get_user_auction_lot_by_id(user_id, lot_id):
    return _auction_system().get_user_auction_lot_by_id(user_id=user_id, lot_id=lot_id)


def build_user_auction_lot_details(user_id, lot_id):
    return _auction_system().build_user_auction_lot_details(user_id=user_id, lot_id=lot_id)


def cancel_active_auction_lot(user_id, lot_id):
    return _auction_system().cancel_active_auction_lot(user_id=user_id, lot_id=lot_id)


def get_user_unclaimed_auction_items(user_id, limit=8, offset=0):
    return _auction_system().get_user_unclaimed_auction_items(
        user_id=user_id, limit=limit, offset=offset
    )


def build_user_unclaimed_auction_item_details(user_id, lot_id):
    return _auction_system().build_user_unclaimed_auction_item_details(
        user_id=user_id, lot_id=lot_id
    )


def claim_expired_auction_item(user_id, lot_id):
    return _auction_system().claim_expired_auction_item(user_id=user_id, lot_id=lot_id)


def get_user_unclaimed_auction_sales(user_id, limit=8, offset=0):
    return _auction_system().get_user_unclaimed_auction_sales(
        user_id=user_id, limit=limit, offset=offset
    )


def build_user_unclaimed_auction_sale_details(user_id, lot_id):
    return _auction_system().build_user_unclaimed_auction_sale_details(
        user_id=user_id, lot_id=lot_id
    )


def claim_auction_sale_gold(user_id, lot_id):
    return _auction_system().claim_auction_sale_gold(user_id=user_id, lot_id=lot_id)


def get_auction_lots_for_buy_filtered(buyer_user_id, category="all", sort_key="new", limit=8, offset=0):
    return _auction_system().get_auction_lots_for_buy_filtered(
        buyer_user_id=buyer_user_id, category=category, sort_key=sort_key,
        limit=limit, offset=offset
    )


def build_auction_buy_lot_details_v2(buyer_user_id, lot_id):
    return _auction_system().build_auction_buy_lot_details_v2(
        buyer_user_id=buyer_user_id, lot_id=lot_id
    )


def buy_auction_lot_v2(buyer_user_id, lot_id):
    return _auction_system().buy_auction_lot_v2(buyer_user_id=buyer_user_id, lot_id=lot_id)


def get_auction_lots_for_buy_search(buyer_user_id, search_text, sort_key="new", limit=8, offset=0):
    return _auction_system().get_auction_lots_for_buy_search(
        buyer_user_id=buyer_user_id, search_text=search_text,
        sort_key=sort_key, limit=limit, offset=offset
    )


def normalize_auction_search_query(search_text):
    return _auction_system().normalize_auction_search_query(search_text=search_text)


def get_user_auction_history(user_id, mode="all", limit=8, offset=0):
    return _auction_system().get_user_auction_history(
        user_id=user_id, mode=mode, limit=limit, offset=offset
    )


def get_auction_lot_market_price_stats(lot_id):
    return _auction_system().get_auction_lot_market_price_stats(lot_id=lot_id)


def search_auction_market_price_stats(search_text, limit=10):
    return _auction_system().search_auction_market_price_stats(
        search_text=search_text, limit=limit
    )


def format_auction_history_date(value, with_time=True):
    return _auction_system().format_auction_history_date(value=value, with_time=with_time)


def update_expired_auction_lots(now_iso=None):
    return _auction_system().update_expired_auction_lots(now_iso=now_iso)


def get_auction_cleanup_report():
    return _auction_system().get_auction_cleanup_report()


def get_auction_diagnostics_report():
    return _auction_system().get_auction_diagnostics_report()


def run_auction_sanity_fix():
    return _auction_system().run_auction_sanity_fix()


# Auction category constant
AUCTION_CATEGORY_RUNE = "rune"


# ==============================
# RUNE SYSTEM
# ==============================

def _rune_system():
    from systems import rune_system
    return rune_system


def init_rune_system():
    return _rune_system().init_rune_system()


def seed_rune_system_items(commit=True):
    return _rune_system().seed_rune_system_items(commit=commit)


def get_inventory_runes(inventory_id):
    return _rune_system().get_inventory_runes(inventory_id)


def get_inventory_rune_capacity(inventory_id):
    return _rune_system().get_inventory_rune_capacity(inventory_id)


def get_inventory_rune_socket_summary(inventory_id):
    return _rune_system().get_inventory_rune_socket_summary(inventory_id)


def get_equipped_rune_stat_totals(user_id):
    return _rune_system().get_equipped_rune_stat_totals(user_id)


def validate_rune_fusion_selection(rune_item_ids):
    return _rune_system().validate_rune_fusion_selection(rune_item_ids)


def claim_daily_quest_reward(user_id):
    return _rune_system().claim_daily_quest_reward_with_firius_tokens(user_id)


def get_equipment_rune_slot_info(user_id, inventory_id):
    return _rune_system().get_equipment_rune_slot_info(user_id, inventory_id)


def get_user_rune_slot_equipment(user_id):
    return _rune_system().get_user_rune_slot_equipment(user_id)


def format_equipment_rune_slots_text(user_id, inventory_id):
    return _rune_system().format_equipment_rune_slots_text(user_id, inventory_id)


def get_user_inventory_rune_stacks(user_id):
    return _rune_system().get_user_inventory_rune_stacks(user_id)


def get_rune_insertion_preview(user_id, equipment_inventory_id, slot_index, rune_inventory_id):
    return _rune_system().get_rune_insertion_preview(
        user_id, equipment_inventory_id, slot_index, rune_inventory_id
    )


def insert_rune_into_equipment(user_id, equipment_inventory_id, slot_index, rune_inventory_id):
    return _rune_system().insert_rune_into_equipment(
        user_id, equipment_inventory_id, slot_index, rune_inventory_id
    )


def get_available_rune_fusion_recipes(user_id):
    return _rune_system().get_available_rune_fusion_recipes(user_id)


def get_firius_token_quantity(user_id):
    return _rune_system().get_firius_token_quantity(user_id)


def get_rune_fusion_preview(user_id, source_item_id):
    return _rune_system().get_rune_fusion_preview(user_id, source_item_id)


def fuse_runes_with_firius_token(user_id, source_item_id):
    return _rune_system().fuse_runes_with_firius_token(user_id, source_item_id)


def get_extractor_material_counts(user_id):
    return _rune_system().get_extractor_material_counts(user_id)


def get_extractor_equipment(user_id):
    return _rune_system().get_extractor_equipment(user_id)


def get_extractor_preview(user_id, equipment_inventory_id):
    return _rune_system().get_extractor_preview(user_id, equipment_inventory_id)


def use_simple_rune_extractor(user_id, equipment_inventory_id, random_choice=None):
    return _rune_system().use_simple_rune_extractor(
        user_id, equipment_inventory_id, random_choice=random_choice
    )


def get_rune_equipment_display_name(inventory_id, fallback_name=None):
    return _rune_system().get_rune_equipment_display_name(
        inventory_id, fallback_name=fallback_name
    )


def use_perfect_rune_extractor(user_id, equipment_inventory_id):
    return _rune_system().use_perfect_rune_extractor(user_id, equipment_inventory_id)


def get_rune_master_shop_state(user_id):
    return _rune_system().get_rune_master_shop_state(user_id)


def buy_simple_rune_extractor(user_id, quantity=1):
    return _rune_system().buy_simple_rune_extractor(user_id, quantity=quantity)


# ==============================
# CONTRACT/QUEST SYSTEM
# ==============================

def _contract_system():
    from systems import contract_system
    return contract_system


def init_contract_system():
    try:
        return _contract_system().init_contract_system()
    except Exception:
        pass


def claim_contract_reward(user_id):
    return _contract_system().claim_contract_reward(user_id)


def get_contract_status(user_id):
    return _contract_system().get_contract_status(user_id)


def process_contract_progress_on_kill(user_id, mob):
    """
    Обробляє прогрес контракту при вбивстві моба.
    """
    return _contract_system().process_contract_progress_on_kill(user_id, mob)


# ==============================
# PLAYER INTERACTION SYSTEM
# ==============================

def _player_interaction():
    from systems import player_interaction_system
    return player_interaction_system


def init_player_interaction_foundation():
    return _player_interaction().init_player_interaction_foundation()


def touch_player_activity(user_id):
    return _player_interaction().touch_player_activity(user_id)


def get_player_last_activity(user_id):
    return _player_interaction().get_player_last_activity(user_id)


def is_player_online(user_id):
    return _player_interaction().is_player_online(user_id)


def get_player_activity_session(user_id):
    return _player_interaction().get_player_activity_session(user_id)


def acquire_player_activity_session(user_id, session_type, context=None):
    return _player_interaction().acquire_player_activity_session(
        user_id, session_type, context=context
    )


def refresh_player_activity_session(user_id):
    return _player_interaction().refresh_player_activity_session(user_id)


def release_player_activity_session(user_id):
    return _player_interaction().release_player_activity_session(user_id)


def expire_stale_player_activity_sessions():
    return _player_interaction().expire_stale_player_activity_sessions()


def is_player_interaction_busy(user_id):
    return _player_interaction().is_player_interaction_busy(user_id)


def get_online_players_in_same_location(user_id):
    return _player_interaction().get_online_players_in_same_location(user_id)


def get_public_player_interaction_profile(user_id):
    return _player_interaction().get_public_player_interaction_profile(user_id)


def init_player_interaction_requests():
    return _player_interaction().init_player_interaction_requests()


def create_player_interaction_request(initiator_user_id, target_user_id, request_type, context=None):
    return _player_interaction().create_player_interaction_request(
        initiator_user_id, target_user_id, request_type, context=context
    )


def get_interaction_request(request_id):
    return _player_interaction().get_interaction_request(request_id)


def respond_to_player_interaction_request(request_id, target_user_id, response):
    return _player_interaction().respond_to_player_interaction_request(
        request_id, target_user_id, response
    )


def cancel_player_interaction_request(request_id, user_id):
    return _player_interaction().cancel_player_interaction_request(request_id, user_id)


def expire_stale_interaction_requests():
    return _player_interaction().expire_stale_interaction_requests()


def recover_orphan_player_activity_sessions():
    return _player_interaction().recover_orphan_player_activity_sessions()


def cleanup_player_interaction_state():
    return _player_interaction().cleanup_player_interaction_state()


def init_player_trade_foundation():
    return _player_interaction().init_player_trade_foundation()


def create_player_trade_from_accepted_request(request_id):
    return _player_interaction().create_player_trade_from_accepted_request(request_id)


def get_player_trade(trade_id):
    return _player_interaction().get_player_trade(trade_id)


def get_active_player_trade(user_id):
    return _player_interaction().get_active_player_trade(user_id)


def get_player_trade_events(trade_id):
    return _player_interaction().get_player_trade_events(trade_id)


def get_player_trade_history(user_id, limit=10, offset=0):
    return _player_interaction().get_player_trade_history(user_id, limit=limit, offset=offset)


def cancel_player_trade(trade_id, user_id):
    return _player_interaction().cancel_player_trade(trade_id, user_id)


def expire_stale_player_trades():
    return _player_interaction().expire_stale_player_trades()


def init_player_trade_item_policy_and_reservations():
    return _player_interaction().init_player_trade_item_policy_and_reservations()


def get_item_trade_policy(item_id):
    return _player_interaction().get_item_trade_policy(item_id)


def build_trade_item_snapshot(inventory_id):
    return _player_interaction().build_trade_item_snapshot(inventory_id)


def get_inventory_reserved_quantity(inventory_id):
    return _player_interaction().get_inventory_reserved_quantity(inventory_id)


def get_inventory_available_quantity(inventory_id):
    return _player_interaction().get_inventory_available_quantity(inventory_id)


def reserve_inventory_for_trade(trade_id, user_id, inventory_id, quantity):
    return _player_interaction().reserve_inventory_for_trade(
        trade_id, user_id, inventory_id, quantity
    )


def release_trade_inventory_reservations(trade_id):
    return _player_interaction().release_trade_inventory_reservations(trade_id)


def assert_inventory_not_reserved(inventory_id):
    return _player_interaction().assert_inventory_not_reserved(inventory_id)


def recover_orphan_inventory_reservations():
    return _player_interaction().recover_orphan_inventory_reservations()


def get_player_trade_offers(trade_id):
    return _player_interaction().get_player_trade_offers(trade_id)


def get_player_trade_editor_state(trade_id, user_id):
    return _player_interaction().get_player_trade_editor_state(trade_id, user_id)


def get_tradeable_inventory_for_trade(trade_id, user_id):
    return _player_interaction().get_tradeable_inventory_for_trade(trade_id, user_id)


def set_player_trade_item_offer(trade_id, user_id, inventory_id, quantity):
    return _player_interaction().set_player_trade_item_offer(
        trade_id, user_id, inventory_id, quantity
    )


def remove_player_trade_item_offer(trade_id, user_id, inventory_id):
    return _player_interaction().remove_player_trade_item_offer(trade_id, user_id, inventory_id)


def set_player_trade_gold_offer(trade_id, user_id, gold_amount):
    return _player_interaction().set_player_trade_gold_offer(trade_id, user_id, gold_amount)


def get_trade_offer_entry(trade_id, user_id, inventory_id):
    return _player_interaction().get_trade_offer_entry(trade_id, user_id, inventory_id)


def add_all_available_to_trade_offer(trade_id, user_id, inventory_id):
    return _player_interaction().add_all_available_to_trade_offer(trade_id, user_id, inventory_id)


def get_player_trade_wallet_state(trade_id, user_id):
    return _player_interaction().get_player_trade_wallet_state(trade_id, user_id)


def get_trade_item_preview(inventory_id):
    return _player_interaction().get_trade_item_preview(inventory_id)


def parse_trade_item_quantity_input(text, max_quantity):
    return _player_interaction().parse_trade_item_quantity_input(text, max_quantity)


def parse_trade_gold_amount_input(text, max_gold):
    return _player_interaction().parse_trade_gold_amount_input(text, max_gold)


def get_tradeable_inventory_for_trade_category(trade_id, user_id, category):
    return _player_interaction().get_tradeable_inventory_for_trade_category(
        trade_id, user_id, category
    )


def get_player_trade_category_counts(trade_id, user_id):
    return _player_interaction().get_player_trade_category_counts(trade_id, user_id)


def recover_active_player_trades_after_restart():
    return _player_interaction().recover_active_player_trades_after_restart()
