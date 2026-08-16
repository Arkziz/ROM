"""
ROM Database Module - Compatibility Layer

✅ REFACTORED STRUCTURE

Модульна архітектура:
├── db_modules/           - Основні модулі
│   ├── connection.py     - Database connection
│   ├── player.py         - Player stats & progression
│   ├── character.py      - Character names & classes
│   ├── equipment.py      - Equipment management
│   ├── inventory.py      - Inventory operations
│   ├── location.py       - Location management
│   ├── utils.py          - Utility functions
│   ├── migrations.py     - DB migrations
│   ├── refine.py         - Refine/enhancement system
│   ├── quests.py         - Daily quests
│   ├── shop.py           - Shop system
│   ├── systems_wrappers.py - Wrappers для systems/*
│   └── __init__.py       - Експорт всіх функцій
└── db.py                 - Цей файл (backwards compatibility)

Використання:
    import db
    
    # Всі функції доступні як і раніше
    user = db.get_user(user_id)
    db.add_item(user_id, item_id, quantity)
    db.create_guild(user_id, name, tag)

Статистика:
    - 13 модулів
    - 472 функції
    - 3,420 рядків модульного коду
    - 100% backwards compatible
"""

# ==============================
# BACKWARDS COMPATIBILITY LAYER
# ==============================
#
# Весь функціонал тепер в db_modules/
# Цей файл просто імпортує і ре-експортує все для сумісності
#

from db_modules import *


# ==============================
# DONE - All functionality is now in db_modules/
# ==============================
