# ✅ ROM REFACTOR SAFETY AUDIT TOOLS V1
# ROM Refactor Tools

Ці інструменти додані перед рефакторингом `db.py`.

## Навіщо

Мета етапу `9.0.0` — нічого не ламати і підготувати safety baseline перед перенесенням логіки з `db.py` у `systems/*`.

## Інструменти

### `audit_duplicate_defs.py`

Шукає duplicate `def` / `class`.

```powershell
python tools/audit_duplicate_defs.py
python tools/audit_duplicate_defs.py db.py
python tools/audit_duplicate_defs.py db.py handlers systems
```

### `check_imports.py`

Компілює `.py` файли і пробує імпортувати core-модулі.

```powershell
python tools/check_imports.py
```

### `smoke_test_rom_core.py`

Перевіряє, що ключовий public API у `db.py` все ще існує.

```powershell
python tools/smoke_test_rom_core.py
```

## Правила рефакторингу

1. Один patch = один домен.
2. `db.py` спочатку лишається compatibility facade.
3. Handlers не переписуємо різко.
4. Після кожного patch:

```powershell
python -m py_compile .\db.py
python tools/check_imports.py
python tools/smoke_test_rom_core.py
```

5. Видаляти старі override-блоки тільки після того, як є нова стабільна реалізація і smoke-tests проходять.
