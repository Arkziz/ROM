# 🚀 Швидкий Довідник - Продовження Рефакторингу

## 🔄 Цикл Виправлення ImportError

```bash
# 1. Запусти бота
.venv\Scripts\python.exe main.py

# 2. Отримай помилку:
# ImportError: cannot import name 'missing_function' from 'db'

# 3. Знайди функцію
grep -n "def missing_function(" db.py.backup_before_cleanup

# 4. Прочитай код (рядки з grep результату)
# ... скопіюй функцію ...

# 5. Додай в правильний модуль db_modules/
# (див. "Куди Додавати Функції" нижче)

# 6. Експортуй в db_modules/__init__.py:
#    - Додай в import секцію
#    - Додай в __all__ список
#    - Оновити count (якщо є коментар з числом)

# 7. Тестуй
py -c "from db import missing_function; print('✅')"

# 8. Повтори з кроку 1
```

---

## 📁 Куди Додавати Функції

| Тип Функції | Модуль | Приклади |
|-------------|--------|----------|
| Player stats, HP, gold, attack | `player.py` | get_player_stats, get_max_hp, get_player_attack_profile |
| Character, class, MP, names | `character.py` | get_character_class, get_user_mp, spend_user_mp |
| Equipment, repair, durability | `equipment.py` | equip_item, repair_equipped_item, damage_on_death |
| Inventory, items, stacks | `inventory.py` | add_item, get_inventory, sell_all_trash |
| Daily quests | `quests.py` | get_user_daily_quest, process_quest_progress |
| Shop, class restrictions | `shop.py` | get_shop_offer, create_shop_preview |
| Energy system | `systems_wrappers.py` | get_user_energy, consume_energy_for_hunt |
| Guild system | `systems_wrappers.py` | get_user_guild, guild_* functions |
| Auction system | `systems_wrappers.py` | auction_* functions |
| Rune system | `systems_wrappers.py` | rune_* functions |
| Contract system | `systems_wrappers.py` | get_contract_status, process_contract |
| Player interaction | `systems_wrappers.py` | player_interaction_* functions |

---

## 🛠️ Шаблони Коду

### 1. Real DB Logic (прямий SQL)
```python
# db_modules/module_name.py
from .connection import conn, cursor

def some_function(user_id):
    cursor.execute("""
    SELECT column FROM table
    WHERE user_id=?
    """, (user_id,))
    
    result = cursor.fetchone()
    return result
```

### 2. System Wrapper
```python
# db_modules/module_name.py або systems_wrappers.py

def _system_name():
    from systems import system_module
    return system_module

def wrapped_function(user_id, param):
    return _system_name().original_function(user_id, param)
```

### 3. Додавання в __init__.py

```python
# Крок 1: Додай в import секцію
from .module_name import (
    existing_function1,
    existing_function2,
    new_function  # ← ДОДАЙ ТУТ
)

# Крок 2: Додай в __all__
__all__ = [
    # Module Name (X functions)  ← ОНОВИТЬ COUNT якщо потрібно
    'existing_function1',
    'existing_function2',
    'new_function',  # ← ДОДАЙ ТУТ
]
```

---

## 🔍 Корисні Команди

### Пошук:
```bash
# Знайти функцію
grep -n "def function_name(" db.py.backup_before_cleanup

# Знайти всі функції в модулі
grep "^def " db.py.backup_before_cleanup

# Перевірити чи функція вже експортована
grep "function_name" db_modules/__init__.py

# Подивитись імпорти хендлера
grep "from db import" handlers/handler_name.py
```

### Тестування:
```bash
# Тестувати один import
py -c "from db import function_name; print('✅')"

# Тестувати декілька imports
py -c "from db import func1, func2, func3; print('✅ All OK')"

# Тестувати всі імпорти хендлера (приклад)
py -c "
from db import (
    get_player_stats,
    get_current_hp,
    add_exp
)
print('✅ Handler imports OK')
"
```

---

## 📋 Чек-лист Додавання Функції

- [ ] Знайшов функцію в `db.py.backup_before_cleanup`
- [ ] Скопіював код функції
- [ ] Визначив правильний модуль db_modules/
- [ ] Додав функцію в модуль
- [ ] Перевірив imports всередині функції (conn, cursor, інші модулі)
- [ ] Додав import функції в `db_modules/__init__.py`
- [ ] Додав функцію в `__all__` список
- [ ] Оновив count в коментарі (якщо є)
- [ ] Протестував: `py -c "from db import ..."`
- [ ] Запустив `main.py` знову

---

## 🎯 Стратегія Швидкого Виправлення

### Варіант 1: По одній функції
1. Запусти main.py
2. Бачиш ImportError
3. Додай 1 функцію
4. Повтори

**Переваги:** Точно знаєш що працює  
**Недоліки:** Багато запусків

### Варіант 2: Пакетами (РЕКОМЕНДУЮ)
1. Запусти main.py → ImportError в handlers/X.py
2. Прочитай ВСІ imports з handlers/X.py:
   ```bash
   grep "from db import" handlers/X.py
   ```
3. Додай ВСІ відсутні функції з цього хендлера
4. Протестуй всі разом:
   ```bash
   py -c "from db import func1, func2, ..., funcN; print('✅')"
   ```
5. Запусти main.py → наступний хендлер

**Переваги:** Швидше, менше запусків  
**Недоліки:** Потрібно додати ~5-30 функцій за раз

---

## 📊 Прогрес Трекінг

### Виправлені Хендлери:
- [x] handlers/start.py (13 функцій)
- [x] handlers/city.py (32 функції)
- [x] handlers/profile.py (19 функцій)
- [x] handlers/combat.py (23 функції)

### Наступні Хендлери:
- [ ] handlers/inventory.py
- [ ] handlers/guild.py
- [ ] handlers/dev.py
- [ ] handlers/refine.py
- [ ] handlers/bosses.py
- [ ] handlers/auction.py
- [ ] handlers/rune.py
- [ ] (інші)

**Всього додано:** 87 функцій  
**Залишилось:** ~50-150 функцій (залежить від хендлерів)

---

## 🚨 Типові Помилки

### 1. Забув експортувати в __init__.py
```
ImportError: cannot import name 'X' from 'db'
```
**Фікс:** Додай X в `db_modules/__init__.py` (import + __all__)

### 2. Циклічний імпорт
```
ImportError: cannot import name 'X' from partially initialized module
```
**Фікс:** Використай lazy import всередині функції:
```python
def some_function():
    from .other_module import helper  # всередині функції
    return helper()
```

### 3. Функція вимагає іншу відсутню функцію
```
NameError: name 'helper_function' is not defined
```
**Фікс:** Додай спочатку helper_function, потім основну

### 4. Неправильний import в модулі
```
ModuleNotFoundError: No module named 'db_modules.X'
```
**Фікс:** Використовуй відносні imports: `from .X import ...`

---

## 💾 Збережи Прогрес (Git)

Після виправлення кожних ~5 хендлерів:

```bash
# Подивись зміни
git status
git diff db_modules/

# Зроби commit
git add db_modules/
git commit -m "fix: додати функції для handlers/X, Y, Z"

# Або детальніший:
git commit -m "fix: додати 25 функцій для inventory та guild хендлерів

- db_modules/inventory.py: +10 функцій
- db_modules/systems_wrappers.py: +15 guild функцій
- db_modules/__init__.py: експорт всіх нових функцій
"
```

---

## 🏁 Фінальний Commit (Коли main.py запуститься)

```bash
# Перевір що бот запускається
.venv\Scripts\python.exe main.py
# ✅ Бот запустився без ImportErrors

# Зроби фінальний commit
git add db.py db.py.backup_before_cleanup db_modules/
git commit -m "refactor: очистити db.py до compatibility layer (51 рядок замість 8,311)

Рефакторинг завершено:
- db.py: 8,311 → 51 рядок (-99.4%)
- db_modules/: 13 модулів, 330+ функцій
- 100% зворотна сумісність
- Всі хендлери працюють
"

git push
```

---

## 📞 Підтримка

Якщо щось не зрозуміло:
1. Читай REFACTORING_SUMMARY.md (детальна документація)
2. Дивись на вже виправлені хендлери (start, city, profile, combat)
3. Шукай patterns в існуючих модулях db_modules/

**Успіхів! 🚀**
