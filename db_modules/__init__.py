from systems.premium_item_policy_system import (
    init_premium_item_policy,
    get_premium_item_policy,
    can_grant_item_from_source,
    grant_item_from_source,
    get_premium_item_grants,
)

from systems.crystal_wallet_system import (
    init_crystal_wallet_system,
    get_crystal_wallet,
    get_crystal_balance,
    credit_crystals,
    debit_crystals,
    get_crystal_transactions,
    compensate_crystal_transaction,
)

"""
DB Modules - Розбитий db.py на логічні модулі

Структура:
- connection.py: Database connection and initialization
- player.py: Player stats, progression, HP (wrapper для player_system)
- character.py: Character names, classes, MP (wrapper для character_system)
- equipment.py: Equipment management (wrapper для equipment_system)
- inventory.py: Inventory and items management
- location.py: Location management  
- utils.py: Utility functions
- migrations.py: Database migrations and maintenance
- refine.py: Refine/enhancement system
- quests.py: Daily quests and contracts
- shop.py: Shop system and class restrictions
- systems_wrappers.py: Wrappers for systems/* (energy, regen, guild, auction, rune, etc.)

Всі функції автоматично експортуються для використання через `import db`.
"""

from .quests import reset_daily_quest_if_needed

from .systems_wrappers import get_contract_exp_for_level

from .equipment import get_equipped_slot

from .equipment import check_armor_compatibility_for_class, check_main_hand_compatibility_for_class, check_off_hand_compatibility_for_class, check_two_handed_conflict_for_equip

from .player import get_exp_to_next_level

from .daily_compat import get_daily_quest_status

from .systems_wrappers import create_daily_contract, abandon_active_contract

from .dev_compat import (
    set_player_level_for_test,
    reset_player_level_for_test,
    set_gold_for_test,
    create_dev_armor_item_for_test,
    create_dev_weapon_item_for_test,
    reset_hero_for_test,
    seed_class_reset_sphere_item,
)

from .inventory_compat import (
    is_inventory_item_equipped,
    find_equipped_slot_by_inventory_id,
    get_item_required_level_by_inventory_id,
    get_item_classification_by_inventory_id,
    is_class_reset_sphere_inventory_item,
    use_class_reset_sphere_from_inventory,
    ARMOR_ALLOWED_BY_CLASS,
    MAIN_HAND_ALLOWED_BY_CLASS,
    OFF_HAND_ALLOWED_BY_CLASS,
)

from data.classes import CLASS_RESET_SPHERE_ITEM_ID

# Connection
from .connection import conn, cursor, SLOT_ORDER, DEFAULT_BAG_SLOTS, init_db, seed_items

# Player
from .player import (
    get_player_level, get_player_stats, get_user_progress, add_exp,
    get_wallet, add_gold, add_kill,
    get_attack, get_magic_attack, get_physical_defense, get_magic_defense,
    get_physical_crit_chance_display, get_magical_crit_chance_display,
    get_base_dodge_chance_display, get_enemy_crit_chance_against_player,
    get_max_hp, get_current_hp_raw, get_current_hp, set_current_hp,
    sync_user_max_hp, create_user, get_user,
    get_player_attack_profile
)

# Character
from .character import (
    CLASS_CONFIGS,
    init_character_class_system,
    normalize_character_name, validate_character_name,
    get_character_name, set_character_name, is_character_name_taken,
    needs_character_name, needs_character_class,
    get_character_class, set_character_class, get_character_class_display,
    get_character_resource_type,
    get_user_mp, set_user_mp, spend_user_mp, restore_user_mp_to_full,
    get_max_mp, refresh_user_mp,
    grant_class_change_available, consume_class_change_available,
    get_class_change_available, has_class_change_available,
    get_character_profile_summary
)

# Equipment
from .equipment import (
    EQUIPMENT_SLOTS, ARMOR_SLOTS, ARMOR_TYPE_LABELS, ITEM_SUBTYPE_LABELS,
    normalize_equipment_restriction_value,
    is_armor_slot, get_armor_type_label, get_item_subtype_label,
    ensure_equipment_slots, get_all_equipped_items, get_all_equipped_slots,
    get_equipped_items_for_repair, get_total_repair_cost,
    get_inventory_detailed, get_inventory_entry, get_item_by_inventory_id,
    get_item_by_inventory_id_full, get_item_bonuses, get_equipped_item_defenses,
    get_sellable_equipment_items,
    init_weapon_damage_system, calculate_weapon_damage_by_values,
    get_weapon_damage_by_inventory_id, get_inventory_weapon_damage_display,
    get_inventory_refine_level, get_inventory_refined_display_name,
    format_refined_item_name,
    can_equip_item_by_class, can_equip_inventory_item_by_class,
    is_inventory_item_class_compatible,
    equip_inventory_item, unequip_inventory_item,
    unequip_incompatible_items_after_class_change,
    repair_equipped_item, repair_all_equipped, calculate_repair_cost,
    damage_equipped_items_on_death,
    apply_random_durability_wear_on_victory,
    sell_inventory_item_to_trader, buy_common_equipment_from_trader,
    buy_item_for_gold
)

from .generated_equipment import create_generated_equipment_item, create_generated_equipment_item_for_slot

# Inventory
from .inventory import (
    get_bag_capacity, get_inventory_used_slots,
    get_inventory, get_item,
    add_item, consume_inventory_item,
    count_user_item, consume_user_item_by_item_id,
    find_first_item_stack_by_type,
    sell_all_trash
)

# Location
from .location import get_current_location, set_current_location

# Utils
from .utils import format_gold, get_today_str, get_daily_today_str

# Migrations
from .migrations import (
    expand_bag_slots_to_40, seed_location_trash_items,
    init_migration_system, run_pending_migrations,
    get_migration_status, run_db_startup_maintenance
)

# Refine system
from .refine import (
    REFINE_STONE_ITEM_ID, SUCCESS_RUNE_ITEM_ID,
    init_refine_system, seed_refine_items,
    get_inventory_item_refine_info, set_inventory_refine_level,
    get_refine_resource_counts,
    get_refine_total_armor_hp_bonus_percent,
    get_refine_effects_summary_for_user,
    get_inventory_refine_display_line,
    ensure_refine_material_stack_sizes,
    get_refine_material_stack_debug
)

# Daily quests
from .quests import (
    init_daily_quest_system,
    get_user_daily_quest, add_daily_quest_progress,
    is_daily_quest_complete, claim_daily_quest_reward,
    get_daily_quest_progress_text,
    cleanup_old_daily_quests,
    process_daily_quest_progress_on_kill
)

# Shop system
from .shop import (
    get_common_equipment_price_for_slot,
    get_allowed_main_hand_subtypes_for_class, get_allowed_off_hand_subtypes_for_class,
    get_allowed_shop_main_hand_profiles, get_allowed_shop_off_hand_profiles,
    get_common_equipment_shop_offer, get_common_equipment_shop_suboffers,
    cleanup_shop_previews_for_user, is_shop_profile_allowed_for_user,
    create_common_equipment_shop_preview, get_shop_preview_item,
    cancel_common_equipment_shop_preview, confirm_common_equipment_shop_preview,
    get_shop_preview_weapon_damage_text,
    init_shop_preview_system,
    get_shop_preview_items, get_shop_preview_item_by_id,
    purchase_shop_preview_item, clear_shop_preview_items,
    init_class_reset_sphere, use_class_reset_sphere,
    can_class_equip_item, get_equippable_class_items,
    generate_class_shop_equipment, populate_class_shop_for_user
)

# System wrappers - import all
from .systems_wrappers import *

# Build __all__ dynamically from all imported names
__all__ = [
    # Connection
    'conn', 'cursor', 'SLOT_ORDER', 'DEFAULT_BAG_SLOTS', 'init_db', 'seed_items',
    
    # Player (20 functions)
    'get_player_level', 'get_player_stats', 'get_user_progress', 'add_exp',
    'get_wallet', 'add_gold', 'add_kill',
    'get_attack', 'get_magic_attack', 'get_physical_defense', 'get_magic_defense',
    'get_physical_crit_chance_display', 'get_magical_crit_chance_display',
    'get_base_dodge_chance_display', 'get_enemy_crit_chance_against_player',
    'get_max_hp', 'get_current_hp_raw', 'get_current_hp', 'set_current_hp',
    'sync_user_max_hp', 'create_user', 'get_user',
    'get_player_attack_profile',
    
    # Character (21 functions + 1 constant)
    'CLASS_CONFIGS',
    'init_character_class_system',
    'normalize_character_name', 'validate_character_name',
    'get_character_name', 'set_character_name', 'is_character_name_taken',
    'needs_character_name', 'needs_character_class',
    'get_character_class', 'set_character_class', 'get_character_class_display',
    'get_character_resource_type',
    'get_user_mp', 'set_user_mp', 'spend_user_mp', 'restore_user_mp_to_full',
    'get_max_mp', 'refresh_user_mp',
    'grant_class_change_available', 'consume_class_change_available',
    'get_class_change_available', 'has_class_change_available',
    'get_character_profile_summary',
    
    # Equipment (43 functions + 4 constants)
    'EQUIPMENT_SLOTS', 'ARMOR_SLOTS', 'ARMOR_TYPE_LABELS', 'ITEM_SUBTYPE_LABELS',
    'normalize_equipment_restriction_value',
    'is_armor_slot', 'get_armor_type_label', 'get_item_subtype_label',
    'ensure_equipment_slots', 'get_all_equipped_items', 'get_all_equipped_slots',
    'get_equipped_items_for_repair', 'get_total_repair_cost',
    'get_inventory_detailed', 'get_inventory_entry', 'get_item_by_inventory_id',
    'get_item_by_inventory_id_full', 'get_item_bonuses', 'get_equipped_item_defenses',
    'get_sellable_equipment_items',
    'damage_equipped_items_on_death', 'apply_random_durability_wear_on_victory',
    'init_weapon_damage_system', 'calculate_weapon_damage_by_values',
    'get_weapon_damage_by_inventory_id', 'get_inventory_weapon_damage_display',
    'get_inventory_refine_level', 'get_inventory_refined_display_name',
    'format_refined_item_name',
    'can_equip_item_by_class', 'can_equip_inventory_item_by_class',
    'is_inventory_item_class_compatible',
    'equip_inventory_item', 'unequip_inventory_item',
    'unequip_incompatible_items_after_class_change',
    'repair_equipped_item', 'repair_all_equipped', 'calculate_repair_cost',
    'sell_inventory_item_to_trader', 'buy_common_equipment_from_trader',
    'buy_item_for_gold',
    
    # Inventory (10 functions)
    'get_bag_capacity', 'get_inventory_used_slots',
    'get_inventory', 'get_item',
    'add_item', 'consume_inventory_item',
    'count_user_item', 'consume_user_item_by_item_id',
    'find_first_item_stack_by_type',
    'sell_all_trash',
    
    # Location (2 functions)
    'get_current_location', 'set_current_location',
    
    # Utils (3 functions)
    'format_gold', 'get_today_str', 'get_daily_today_str',
    
    # Migrations (6 functions)
    'expand_bag_slots_to_40', 'seed_location_trash_items',
    'init_migration_system', 'run_pending_migrations',
    'get_migration_status', 'run_db_startup_maintenance',
    
    # Refine (11 functions + 2 constants)
    'REFINE_STONE_ITEM_ID', 'SUCCESS_RUNE_ITEM_ID',
    'init_refine_system', 'seed_refine_items',
    'get_inventory_item_refine_info', 'set_inventory_refine_level',
    'get_refine_resource_counts',
    'get_refine_total_armor_hp_bonus_percent',
    'get_refine_effects_summary_for_user',
    'get_inventory_refine_display_line',
    'ensure_refine_material_stack_sizes',
    'get_refine_material_stack_debug',
    
    # Quests (7 functions)
    'init_daily_quest_system',
    'get_user_daily_quest', 'add_daily_quest_progress',
    'is_daily_quest_complete', 'claim_daily_quest_reward',
    'get_daily_quest_progress_text',
    'cleanup_old_daily_quests',
    'process_daily_quest_progress_on_kill',
    
    # Shop (23 functions)
    'get_common_equipment_price_for_slot',
    'get_allowed_main_hand_subtypes_for_class', 'get_allowed_off_hand_subtypes_for_class',
    'get_allowed_shop_main_hand_profiles', 'get_allowed_shop_off_hand_profiles',
    'get_common_equipment_shop_offer', 'get_common_equipment_shop_suboffers',
    'cleanup_shop_previews_for_user', 'is_shop_profile_allowed_for_user',
    'create_common_equipment_shop_preview', 'get_shop_preview_item',
    'cancel_common_equipment_shop_preview', 'confirm_common_equipment_shop_preview',
    'get_shop_preview_weapon_damage_text',
    'init_shop_preview_system',
    'get_shop_preview_items', 'get_shop_preview_item_by_id',
    'purchase_shop_preview_item', 'clear_shop_preview_items',
    'init_class_reset_sphere', 'use_class_reset_sphere',
    'can_class_equip_item', 'get_equippable_class_items',
    'generate_class_shop_equipment', 'populate_class_shop_for_user',
    
    # Systems wrappers (~200+ functions) - add dynamically
    # Energy system (6)
    'init_energy_system', 'get_user_energy', 'consume_energy_for_hunt',
    'restore_energy_for_test', 'get_users_for_energy_full_notification',
    'reset_daily_hunts_if_needed',
    
    # Regen system (5)
    'init_hp_regen_system', 'init_passive_regen_system',
    'process_passive_regeneration', 'reset_hp_regen_timers_now',
    'apply_passive_hp_regen',
    
    # Guild system (~80 functions)
    'init_guild_system', 'get_current_guild_season_key',
    'ensure_all_guild_monthly_seasons', 'ensure_guild_monthly_season',
    'create_guild', 'get_guild_creation_terms', 'get_user_guild', 'get_user_guild_member',
    'get_user_guild_role', 'is_user_in_guild',
    'get_guild_by_id', 'get_guild_by_name_or_tag',
    'get_guild_members', 'get_guild_member_count',
    'create_guild_application', 'get_guild_applications',
    'can_manage_guild_applications', 'add_guild_progress',
    'get_guild_ranking', 'get_guild_season_history',
    'get_guild_display_name', 'get_guild_role_label',
    'get_user_guild_profile_line', 'get_public_guild_list',
    'get_user_guild_applications', 'has_pending_guild_application',
    'cancel_guild_application', 'get_guild_by_icon',
    'is_guild_icon_taken', 'make_existing_guild_icons_unique',
    'ensure_unique_guild_icon_index', 'get_guild_application_by_id',
    'accept_guild_application', 'reject_guild_application',
    'get_guild_member', 'get_character_name_by_user_id',
    'is_guild_leader', 'is_guild_officer',
    'promote_guild_member_to_officer', 'demote_guild_officer',
    'kick_guild_member', 'get_guild_join_cooldown', 'format_guild_join_cooldown_remaining',
    'can_user_join_or_create_guild', 'leave_guild', 'transfer_guild_leadership', 'transfer_guild_leadership_and_leave', 'get_guild_officer_count',
    'get_guild_officer_member', 'cleanup_stale_guild_applications',
    'get_guild_exp_required_for_level', 'calculate_guild_level_from_exp',
    'get_guild_next_level_info', 'recalculate_guild_level',
    'add_user_guild_progress', 'get_guild_contribution_ranking',
    'cleanup_recalculate_all_guild_levels', 'get_guild_logs',
    'get_guild_logs_count', 'award_guild_elite_kill',
    'award_guild_contract_completion', 'get_guild_activity_reward_text',
    'get_guild_pending_applications_count', 'get_user_pending_applications_count',
    'get_guild_diagnostics', 'run_guild_sanity_cleanup',
    
    # Auction system (~60 functions)
    'init_auction_house', 'validate_auction_price',
    'decimal_to_price_text', 'auction_price_to_decimal',
    'normalize_auction_category', 'add_auction_history',
    'get_auction_lot_by_id', 'get_user_active_auction_count',
    'can_user_create_auction_lot', 'get_auction_lots',
    'create_auction_lot_record', 'mark_auction_lot_status',
    'get_auction_house_stats', 'get_user_sellable_equipment_for_auction',
    'get_inventory_item_snapshot_for_auction',
    'validate_inventory_item_for_auction_equipment',
    'create_equipment_auction_lot',
    'get_user_sellable_stack_items_for_auction',
    'validate_inventory_stack_item_for_auction',
    'create_stack_auction_lot',
    'get_public_auction_lots_for_buyer',
    'build_auction_lot_public_details',
    'buy_auction_lot',
    'build_auction_sell_item_review_text',
    'get_user_auction_lots',
    'get_user_auction_lot_by_id',
    'build_user_auction_lot_details',
    'cancel_active_auction_lot',
    'get_user_unclaimed_auction_items',
    'build_user_unclaimed_auction_item_details',
    'claim_expired_auction_item',
    'get_user_unclaimed_auction_sales',
    'build_user_unclaimed_auction_sale_details',
    'claim_auction_sale_gold',
    'get_auction_lots_for_buy_filtered',
    'build_auction_buy_lot_details_v2',
    'buy_auction_lot_v2',
    'get_auction_lots_for_buy_search',
    'normalize_auction_search_query',
    'get_user_auction_history',
    'get_auction_lot_market_price_stats',
    'search_auction_market_price_stats',
    'format_auction_history_date',
    'update_expired_auction_lots',
    'get_auction_cleanup_report',
    'get_auction_diagnostics_report',
    'run_auction_sanity_fix',
    'AUCTION_CATEGORY_RUNE',
    
    # Rune system (~30 functions)
    'init_rune_system', 'seed_rune_system_items',
    'get_inventory_runes', 'get_inventory_rune_capacity',
    'get_inventory_rune_socket_summary',
    'get_equipped_rune_stat_totals',
    'validate_rune_fusion_selection',
    'get_equipment_rune_slot_info',
    'get_user_rune_slot_equipment',
    'format_equipment_rune_slots_text',
    'get_user_inventory_rune_stacks',
    'get_rune_insertion_preview',
    'insert_rune_into_equipment',
    'get_available_rune_fusion_recipes',
    'get_firius_token_quantity',
    'get_rune_fusion_preview',
    'fuse_runes_with_firius_token',
    'get_extractor_material_counts',
    'get_extractor_equipment',
    'get_extractor_preview',
    'use_simple_rune_extractor',
    'get_rune_equipment_display_name',
    'use_perfect_rune_extractor',
    'get_rune_master_shop_state',
    'buy_simple_rune_extractor',
    
    # Contract system (4 functions)
    'init_contract_system', 'claim_contract_reward', 'get_contract_status',
    'process_contract_progress_on_kill',
    
    # Player interaction (~50 functions)
    'init_player_interaction_foundation',
    'touch_player_activity', 'get_player_last_activity',
    'is_player_online', 'get_player_activity_session',
    'acquire_player_activity_session', 'refresh_player_activity_session',
    'release_player_activity_session', 'expire_stale_player_activity_sessions',
    'is_player_interaction_busy', 'get_online_players_in_same_location',
    'get_public_player_interaction_profile',
    'init_player_interaction_requests',
    'create_player_interaction_request', 'get_interaction_request',
    'respond_to_player_interaction_request',
    'cancel_player_interaction_request',
    'expire_stale_interaction_requests',
    'recover_orphan_player_activity_sessions',
    'cleanup_player_interaction_state',
    'init_player_trade_foundation',
    'create_player_trade_from_accepted_request',
    'get_player_trade', 'get_active_player_trade',
    'get_player_trade_events', 'get_player_trade_history',
    'cancel_player_trade', 'expire_stale_player_trades',
    'init_player_trade_item_policy_and_reservations',
    'get_item_trade_policy', 'build_trade_item_snapshot',
    'get_inventory_reserved_quantity', 'get_inventory_available_quantity',
    'reserve_inventory_for_trade', 'release_trade_inventory_reservations',
    'assert_inventory_not_reserved', 'recover_orphan_inventory_reservations',
    'get_player_trade_offers', 'get_player_trade_editor_state',
    'get_tradeable_inventory_for_trade',
    'set_player_trade_item_offer', 'remove_player_trade_item_offer',
    'set_player_trade_gold_offer', 'get_trade_offer_entry',
    'add_all_available_to_trade_offer',
    'get_player_trade_wallet_state', 'get_trade_item_preview',
    'parse_trade_item_quantity_input', 'parse_trade_gold_amount_input',
    'get_tradeable_inventory_for_trade_category',
    'get_player_trade_category_counts',
    'recover_active_player_trades_after_restart',
    'create_generated_equipment_item',
    'create_generated_equipment_item_for_slot',
    'CLASS_RESET_SPHERE_ITEM_ID',
    'is_inventory_item_equipped',
    'find_equipped_slot_by_inventory_id',
    'get_item_required_level_by_inventory_id',
    'get_item_classification_by_inventory_id',
    'is_class_reset_sphere_inventory_item',
    'use_class_reset_sphere_from_inventory',
    'ARMOR_ALLOWED_BY_CLASS',
    'MAIN_HAND_ALLOWED_BY_CLASS',
    'OFF_HAND_ALLOWED_BY_CLASS',
    'set_player_level_for_test',
    'reset_player_level_for_test',
    'set_gold_for_test',
    'create_dev_armor_item_for_test',
    'create_dev_weapon_item_for_test',
    'reset_hero_for_test',
    'seed_class_reset_sphere_item',
]

__all__.extend(['create_daily_contract', 'abandon_active_contract'])

__all__.append('get_daily_quest_status')

__all__.append('get_exp_to_next_level')

__all__.extend(['check_armor_compatibility_for_class', 'check_main_hand_compatibility_for_class', 'check_off_hand_compatibility_for_class', 'check_two_handed_conflict_for_equip'])

__all__.append('get_equipped_slot')

__all__.append('get_contract_exp_for_level')

__all__.append('reset_daily_quest_if_needed')

__all__.extend(['init_crystal_wallet_system','get_crystal_wallet','get_crystal_balance','credit_crystals','debit_crystals','get_crystal_transactions','compensate_crystal_transaction'])

__all__.extend(['init_premium_item_policy','get_premium_item_policy','can_grant_item_from_source','grant_item_from_source','get_premium_item_grants'])
