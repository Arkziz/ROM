# План рефакторингу проєкту ROM - Серпень 2026

## 📊 Поточний стан проєкту (16.08.2026)

### Аналіз кодової бази

**Статистика:**
- `db.py`: **8,241 рядків**, **431 функція** - критична монолітність
- `main.py`: 227 рядків - прийнятно, але потребує оптимізації
- `handlers/`: 18 модулів - добре структуровано
- `systems/`: 45+ модулів - відмінна база для розширення
- `data/`: 10+ файлів конфігурації - ідеальне відокремлення

### Підтвердження первісного плану

✅ **План з REFACTOR_PLAN.md та TECHNICAL_AUDIT залишається актуальним**

Основні проблеми підтверджені:
1. Монолітний `db.py` - найбільша загроза масштабованості
2. Глобальні змінні та стан
3. Хендлери напряму залежать від `db.py`
4. Системи мають хаотичні залежності
5. Відсутність повноцінного тестування

### Нова інформація

**Позитивні моменти:**
- Вже є багато окремих систем у `systems/`
- PvP-система має власну модульну структуру (приклад для наслідування)
- Є smoke-тести в `tools/`
- Дані винесені в окремі модулі

**Критичні ризики:**
- 431 функція в одному файлі - будь-яка зміна може зламати десятки інших функцій
- Неможливо тестувати окремі домени без завантаження всього `db.py`
- Складність онбордингу нових розробників

---

## 🎯 Стратегія рефакторингу

### Принципи роботи

1. **Incremental refactoring** - невеликі зміни з частими комітами
2. **Zero breaking changes** - ігрова логіка має працювати після кожного коміту
3. **Test-driven** - додаємо тести перед рефакторингом кожного модуля
4. **Backwards compatibility** - старі імпорти працюють через compatibility layer

### Пріоритети

**P0 (Критично):**
- Розбиття `db.py` на domain services
- Створення data access layer
- Базове тестування критичних механік

**P1 (Високий):**
- Очищення глобального стану
- Рефакторинг handlers на thin layer
- Стандартизація ініціалізації

**P2 (Середній):**
- Розширені тести
- Документація API
- Performance оптимізації

---

## 📋 Поетапний план виконання

### Етап 0: Підготовка (1 коміт)

**Мета:** Створити інфраструктуру для рефакторингу

**Завдання:**
1. Створити нову структуру каталогів:
   ```
   app/
     domain/
       models/
       services/
     infrastructure/
       database/
       repositories/
     interfaces/
   tests/
     unit/
     integration/
   ```
2. Додати `requirements-dev.txt` з pytest
3. Створити базовий `conftest.py` для тестів
4. Додати `.gitignore` записи для тестових файлів

**Результат:** Готова структура для міграції коду

**Час:** 1-2 години

---

### Етап 1: Аудит та мапінг залежностей (1 коміт)

**Мета:** Зрозуміти повний граф залежностей між функціями в `db.py`

**Завдання:**
1. Проаналізувати всі 431 функцію в `db.py`
2. Згрупувати функції за доменами:
   - User management
   - Inventory & items
   - Equipment & slots
   - Combat & stats
   - Economy (gold, shop, trading)
   - Quests & contracts
   - Character classes
   - Runes & refinement
   - Regeneration (HP/MP/Energy)
   - Testing utilities
3. Створити документ `DEPENDENCY_MAP.md` з графом залежностей
4. Визначити "leaf functions" (без залежностей) для першої міграції

**Результат:** Чіткий план, які функції мігрувати першими

**Час:** 2-3 години

---

### Етап 2: Створення Data Access Layer (1 коміт)

**Мета:** Ізолювати всі SQL-операції в окремому шарі

**Завдання:**
1. Створити `app/infrastructure/database/connection.py`:
   - Database connection manager
   - Connection pool (для майбутнього)
   - Transaction manager
2. Створити `app/infrastructure/database/base_repository.py`:
   - Base class для всіх repositories
   - CRUD методи
3. Створити compatibility wrapper у `db.py`, що використовує новий connection manager

**Код:**
```python
# app/infrastructure/database/connection.py
class DatabaseConnection:
    def __init__(self, db_path="game.db"):
        self._conn = None
        self._db_path = db_path
    
    def get_connection(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        return self._conn
    
    def execute(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor
```

**Результат:** Централізоване управління підключеннями до БД

**Час:** 2-3 години

---

### Етап 3: Міграція User Domain (2-3 коміти)

**Мета:** Перенести всю логіку роботи з користувачами в окремий домен

#### Коміт 3.1: User Repository

**Завдання:**
1. Створити `app/infrastructure/repositories/user_repository.py`
2. Перенести функції:
   - `create_user()`
   - `get_user()`
   - `update_user()`
   - Всі get/set функції для user полів (gold, kills, hp, stats, etc.)

**Тести:**
```python
def test_create_user():
    repo = UserRepository()
    user_id = 123456
    repo.create_user(user_id)
    user = repo.get_user(user_id)
    assert user is not None
    assert user['level'] == 1
```

#### Коміт 3.2: User Service

**Завдання:**
1. Створити `app/domain/services/user_service.py`
2. Перенести бізнес-логіку:
   - Character creation workflow
   - Level up logic
   - Stat calculations
3. User service використовує user repository

#### Коміт 3.3: Compatibility Layer

**Завдання:**
1. У `db.py` залишити старі функції як проксі до нових:
```python
def create_user(user_id, **kwargs):
    """DEPRECATED: Use UserService instead"""
    from app.domain.services.user_service import UserService
    return UserService().create_user(user_id, **kwargs)
```

**Результат:** User domain повністю відокремлений, старий код працює

**Час:** 4-6 годин

---

### Етап 4: Міграція Inventory Domain (2-3 коміти)

**Мета:** Відокремити логіку інвентарю

#### Коміт 4.1: Item Repository

**Завдання:**
1. `app/infrastructure/repositories/item_repository.py`
2. Функції для роботи з items таблицею

#### Коміт 4.2: Inventory Repository

**Завдання:**
1. `app/infrastructure/repositories/inventory_repository.py`
2. Всі CRUD операції з inventory

#### Коміт 4.3: Inventory Service

**Завдання:**
1. `app/domain/services/inventory_service.py`
2. Бізнес-логіка:
   - `add_item()` з логікою стакування
   - `consume_inventory_item()`
   - `find_first_item_stack_by_type()`
   - Bag capacity logic

**Результат:** Inventory domain відокремлений

**Час:** 5-7 годин

---

### Етап 5: Міграція Equipment Domain (2-3 коміти)

**Мета:** Відокремити систему спорядження

#### Коміт 5.1: Equipment Repository

**Завдання:**
1. `app/infrastructure/repositories/equipment_repository.py`
2. Робота з `equipment_slots` таблицею
3. Функції для екіпірування/зняття

#### Коміт 5.2: Equipment Service

**Завдання:**
1. `app/domain/services/equipment_service.py`
2. Бізнес-логіка:
   - `equip_item()` з валідацією класів
   - `unequip_slot()`
   - Stat calculation from equipment
   - Durability system

**Результат:** Equipment domain відокремлений

**Час:** 5-7 годин

---

### Етап 6: Міграція Combat Domain (2-3 коміти)

**Мета:** Відокремити бойову систему

**Завдання:**
1. `app/domain/services/combat_service.py`
2. Перенести логіку з `systems/combat_system.py` та `db.py`:
   - Attack calculations
   - Defense calculations
   - Crit/dodge mechanics
   - Damage application
3. Інтеграція з `UserService`, `EquipmentService`

**Результат:** Combat domain відокремлений

**Час:** 5-7 годин

---

### Етап 7: Міграція Economy Domain (2 коміти)

**Мета:** Відокремити економічну систему

#### Коміт 7.1: Economy Service

**Завдання:**
1. `app/domain/services/economy_service.py`
2. Функції:
   - Gold management
   - Sell/buy logic
   - Shop system
   - Repair costs

**Результат:** Economy domain відокремлений

**Час:** 3-5 годин

---

### Етап 8: Міграція Quest & Contract Domain (2-3 коміти)

**Мета:** Відокремити квести та контракти

**Завдання:**
1. `app/domain/services/quest_service.py`
2. `app/domain/services/contract_service.py`
3. Daily quests, daily contracts
4. Progress tracking
5. Reward distribution

**Результат:** Quest domain відокремлений

**Час:** 4-6 годин

---

### Етап 9: Міграція Class System Domain (2 коміти)

**Мета:** Відокремити систему класів

**Завдання:**
1. `app/domain/services/class_service.py`
2. Class-specific logic
3. Class restrictions
4. Class switching

**Результат:** Class domain відокремлений

**Час:** 3-4 години

---

### Етап 10: Міграція Rune System Domain (2 коміти)

**Мета:** Відокремити систему рун

**Завдання:**
1. `app/domain/services/rune_service.py`
2. Rune application
3. Rune fusion
4. Rune extraction

**Результат:** Rune domain відокремлений

**Час:** 3-4 години

---

### Етап 11: Рефакторинг Handlers (3-4 коміти)

**Мета:** Handlers стають тонким шаром між Telegram та Services

**Завдання для кожного handler:**
1. Замінити прямі імпорти з `db.py` на імпорти services
2. Залишити в handler тільки:
   - Message parsing
   - Input validation
   - Service calls
   - Response formatting

**Приклад:**
```python
# До:
@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    # ... багато логіки ...

# Після:
@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    user_service = UserService()
    user = user_service.get_user(user_id)
    text = format_profile_text(user)
    bot.send_message(message.chat.id, text)
```

**Результат:** Тонкі, зрозумілі handlers

**Час:** 8-12 годин

---

### Етап 12: Рефакторинг main.py Bootstrap (1 коміт)

**Мета:** Очистити точку входу

**Завдання:**
1. Створити `app/bootstrap.py`
2. Перенести всю ініціалізацію туди:
   - Database initialization
   - Migrations
   - Seed data
   - System initialization
3. `main.py` стає мінімальним:
```python
from app.bootstrap import initialize_application
from app.interfaces.telegram_bot import create_bot

def main():
    initialize_application()
    bot = create_bot()
    bot.run()

if __name__ == '__main__':
    main()
```

**Результат:** Чистий entry point

**Час:** 2-3 години

---

### Етап 13: Прибирання глобального стану (2-3 коміти)

**Мета:** Усунути глобальні змінні

**Завдання:**
1. Знайти всі глобальні state dictionaries/sets
2. Перенести їх у відповідні services або session managers
3. Для temp state створити `app/domain/session_manager.py`

**Результат:** Немає глобального мутабельного стану

**Час:** 4-6 годин

---

### Етап 14: Розширене тестування (3-5 комітів)

**Мета:** Покрити критичні сценарії тестами

**Завдання:**
1. Unit тести для кожного service
2. Integration тести для критичних сценаріїв:
   - User creation -> leveling -> equipment -> combat
   - Trading flow
   - Quest completion
   - Class switching
3. Smoke тести для handlers

**Результат:** >70% code coverage для domain services

**Час:** 10-15 годин

---

### Етап 15: Документація та очищення (2 коміти)

**Мета:** Завершити рефакторинг

**Завдання:**
1. Видалити всі compatibility layers з `db.py`
2. Створити `ARCHITECTURE.md` з описом нової структури
3. Оновити README з новими інструкціями
4. Додати docstrings до всіх публічних методів

**Результат:** Чистий, задокументований код

**Час:** 4-6 годин

---

## 📊 Загальна оцінка

### Часові рамки

- **Мінімальний план (Етапи 0-10):** 50-70 годин = 1-2 тижні full-time
- **Повний план (Етапи 0-15):** 80-110 годин = 2-3 тижні full-time
- **З part-time роботою:** 1-2 місяці

### Кількість комітів

**Орієнтовно:** 25-35 комітів

### Ризики

**Низький ризик:**
- Incremental approach
- Кожен коміт тестується
- Backwards compatibility

**Потенційні проблеми:**
- Складність тестування з SQLite
- Циклічні залежності між services
- Performance regression

### Переваги після рефакторингу

✅ Легко додавати нові фічі
✅ Простіше знаходити баги
✅ Можливість паралельної розробки
✅ Кращий onboarding
✅ Готовність до масштабування
✅ Можливість замінити SQLite на PostgreSQL

---

## 🚀 Порядок виконання

### Рекомендований підхід

1. **Тиждень 1:** Етапи 0-5 (Підготовка + User + Inventory + Equipment)
2. **Тиждень 2:** Етапи 6-10 (Combat + Economy + Quests + Classes + Runes)
3. **Тиждень 3:** Етапи 11-13 (Handlers + Bootstrap + Global state)
4. **Тиждень 4:** Етапи 14-15 (Testing + Documentation)

### Альтернативний підхід (більш консервативний)

1. **Спринт 1:** Етапи 0-3 (Інфраструктура + Users)
2. **Спринт 2:** Етапи 4-5 (Inventory + Equipment)
3. **Спринт 3:** Етапи 6-7 (Combat + Economy)
4. **Спринт 4:** Етапи 8-10 (Quests + Classes + Runes)
5. **Спринт 5:** Етапи 11-12 (Handlers + Bootstrap)
6. **Спринт 6:** Етапи 13-15 (State + Tests + Docs)

---

## ✅ Критерії успіху

Рефакторинг буде вважатися успішним, якщо:

1. ✅ `db.py` містить <500 рядків (тільки schema і migrations)
2. ✅ Кожен domain має окремий service <300 рядків
3. ✅ Handlers не містять SQL queries
4. ✅ >70% code coverage для domain services
5. ✅ Всі існуючі фічі працюють без змін
6. ✅ Час запуску бота не збільшився >10%
7. ✅ Немає глобальних мутабельних змінних
8. ✅ Нова фіча додається за <2 години без ризику зламати старі

---

## 🎯 Початок роботи

### Перший крок (прямо зараз)

Я можу почати з **Етапу 0: Підготовка** - створити структуру каталогів та базову інфраструктуру для тестів.

Потім ми продовжимо з **Етапу 1: Аудит** - я проаналізую всі 431 функцію в `db.py` та створю детальну карту залежностей.

### Твоє рішення

Чи готовий я приступити до виконання? **Так, я можу це зробити!**

Але мені потрібно твоє підтвердження на початок роботи та вибір підходу:

**Варіант А (Агресивний):** 
Починаємо з Етапу 0 прямо зараз, робимо 2-3 етапи на день

**Варіант Б (Консервативний):** 
Починаємо з Етапу 0, після кожного етапу ти тестуєш гру та робиш коміт

**Варіант В (Гібридний):**
Я роблю Етапи 0-2 (підготовка + аудит + DAL) за один сеанс, ти тестуєш, потім продовжуємо

Який варіант обираєш?
