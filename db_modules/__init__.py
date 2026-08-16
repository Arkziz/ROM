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

Більшість функцій делегує роботу в systems/ модулі для consistency.
"""

# Connection
from .connection import conn, cursor, SLOT_ORDER, DEFAULT_BAG_SLOTS, init_db, seed_items

# Player
from .player import (
    get_player_level, get_player_stats, get_user_progress, add_exp,
    get_wallet, add_gold, add_kill,
    get_attack, get_magic_attack, get_physical_defense, get_magic_defense,
    get_physical_crit_chance_display, get_magical_crit_chance_display,
    get_base_dodge_chance_display,
    get_max_hp, get_current_hp_raw, get_current_hp, set_current_hp,
    sync_user_max_hp, create_user, get_user
)

# Character
from .character import (
    normalize_character_name, validate_character_name,
    get_character_name, set_character_name, is_character_name_taken,
    get_character_class, set_character_class, get_character_class_display,
    get_character_resource_type,
    get_user_mp, set_user_mp, get_max_mp, refresh_user_mp,
    grant_class_change_available, consume_class_change_available,
    get_class_change_available, has_class_change_available
)

# Equipment
from .equipment import (
    ensure_equipment_slots, get_all_equipped_items, get_equipped_items_for_repair,
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
    sell_inventory_item_to_trader, buy_common_equipment_from_trader,
    buy_item_for_gold
)

# Inventory
from .inventory import (
    get_bag_capacity, get_inventory_used_slots,
    get_inventory, get_item,
    add_item, consume_inventory_item,
    count_user_item, consume_user_item_by_item_id,
    find_first_item_stack_by_type
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

__all__ = [
    # Connection
    'conn', 'cursor', 'SLOT_ORDER', 'DEFAULT_BAG_SLOTS', 'init_db', 'seed_items',
    
    # Player
    'get_player_level', 'get_player_stats', 'get_user_progress', 'add_exp',
    'get_wallet', 'add_gold', 'add_kill',
    'get_attack', 'get_magic_attack', 'get_physical_defense', 'get_magic_defense',
    'get_physical_crit_chance_display', 'get_magical_crit_chance_display',
    'get_base_dodge_chance_display',
    'get_max_hp', 'get_current_hp_raw', 'get_current_hp', 'set_current_hp',
    'sync_user_max_hp', 'create_user', 'get_user',
    
    # Character
    'normalize_character_name', 'validate_character_name',
    'get_character_name', 'set_character_name', 'is_character_name_taken',
    'get_character_class', 'set_character_class', 'get_character_class_display',
    'get_character_resource_type',
    'get_user_mp', 'set_user_mp', 'get_max_mp', 'refresh_user_mp',
    'grant_class_change_available', 'consume_class_change_available',
    'get_class_change_available', 'has_class_change_available',
    
    # Equipment
    'ensure_equipment_slots', 'get_all_equipped_items', 'get_equipped_items_for_repair',
    'get_inventory_detailed', 'get_inventory_entry', 'get_item_by_inventory_id',
    'get_item_by_inventory_id_full', 'get_item_bonuses', 'get_equipped_item_defenses',
    'get_sellable_equipment_items',
    'init_weapon_damage_system', 'calculate_weapon_damage_by_values',
    'get_weapon_damage_by_inventory_id', 'get_inventory_weapon_damage_display',
    'get_inventory_refine_level', 'get_inventory_refined_display_name',
    'format_refined_item_name',
    'can_equip_item_by_class', 'can_equip_inventory_item_by_class',
    'is_inventory_item_class_compatible',
    'equip_inventory_item', 'unequip_inventory_item',
    'unequip_incompatible_items_after_class_change',
    'repair_equipped_item', 'repair_all_equipped', 'calculate_repair_cost',
    'damage_equipped_items_on_death',
    'sell_inventory_item_to_trader', 'buy_common_equipment_from_trader',
    'buy_item_for_gold',
    
    # Inventory
    'get_bag_capacity', 'get_inventory_used_slots',
    'get_inventory', 'get_item',
    'add_item', 'consume_inventory_item',
    'count_user_item', 'consume_user_item_by_item_id',
    'find_first_item_stack_by_type',
    
    # Location
    'get_current_location', 'set_current_location',
    
    # Utils
    'format_gold', 'get_today_str', 'get_daily_today_str',
    
    # Migrations
    'expand_bag_slots_to_40', 'seed_location_trash_items',
    'init_migration_system', 'run_pending_migrations',
    'get_migration_status', 'run_db_startup_maintenance',
]
