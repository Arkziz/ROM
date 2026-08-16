"""
DB Modules - Розбитий db.py на логічні модулі

Структура:
- connection.py: Database connection and initialization
- location.py: Location management  
- utils.py: Utility functions
- migrations.py: Database migrations and maintenance

Більшість функцій делегує роботу в systems/ модулі:
- systems/player_system.py: User stats, progression, gold
- systems/equipment_system.py: Equipment, inventory, weapons
- systems/character_system.py: Character names, classes, MP
- systems/rune_system.py: Rune system
- systems/energy_system.py: Energy system
- systems/regen_system.py: HP/MP regeneration
- systems/guild_system.py: Guild management
- systems/auction_house_system.py: Auction house
- systems/player_interaction_system.py: Player trades
"""

# Re-export connection and core functions
from .connection import conn, cursor, SLOT_ORDER, init_db, seed_items
from .location import get_current_location, set_current_location  
from .utils import format_gold, get_today_str, get_daily_today_str
from .migrations import (
    expand_bag_slots_to_40,
    seed_location_trash_items,
    init_migration_system,
    run_pending_migrations,
    get_migration_status,
    run_db_startup_maintenance
)

__all__ = [
    # Connection
    'conn', 'cursor', 'SLOT_ORDER',
    'init_db', 'seed_items',
    
    # Location
    'get_current_location', 'set_current_location',
    
    # Utils
    'format_gold', 'get_today_str', 'get_daily_today_str',
    
    # Migrations
    'expand_bag_slots_to_40',
    'seed_location_trash_items',
    'init_migration_system',
    'run_pending_migrations',
    'get_migration_status',
    'run_db_startup_maintenance',
]
