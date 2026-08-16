# 🪟 PowerShell Команди для Windows

## 🚀 Запуск Бота

```powershell
# Активувати venv
.venv\Scripts\python.exe

# Запустити бота
.venv\Scripts\python.exe main.py

# АБО з активованим venv:
& c:\Users\Oleh\OneDrive\Документи\ROM\.venv\Scripts\Activate.ps1
python main.py
```

---

## 🔍 Пошук Функцій

```powershell
# Знайти функцію в backup (PowerShell)
Select-String -Path "db.py.backup_before_cleanup" -Pattern "def function_name\(" -Context 0,20

# Знайти ВСІ функції
Select-String -Path "db.py.backup_before_cleanup" -Pattern "^def " | Measure-Object

# Перевірити експорт
Select-String -Path "db_modules\__init__.py" -Pattern "function_name"

# Імпорти в хендлері
Select-String -Path "handlers\handler_name.py" -Pattern "from db import"
```

---

## ✅ Тестування Imports

```powershell
# Один import
py -c "from db import function_name; print('✅')"

# Декілька imports
py -c "from db import func1, func2, func3; print('✅')"

# Багато imports (multiline)
py -c @"
from db import (
    function1,
    function2,
    function3
)
print('✅ All imports OK')
"@
```

---

## 📝 Редагування Файлів

```powershell
# Відкрити в VS Code
code db_modules\module_name.py
code db_modules\__init__.py

# Відкрити в Notepad
notepad db_modules\module_name.py

# Копіювати файл
Copy-Item "db.py" "db.py.backup"
```

---

## 📊 Статистика

```powershell
# Порахувати рядки в файлі
(Get-Content "db.py").Count

# Порахувати функції (приблизно)
(Select-String -Path "db.py.backup_before_cleanup" -Pattern "^def ").Count

# Розмір файлу
(Get-Item "db.py").Length / 1KB
```

---

## 🔄 Git Команди

```powershell
# Статус
git status

# Додати зміни
git add db_modules\
git add db.py

# Commit
git commit -m "fix: додати функції для handlers"

# Push
git push
```

---

## 📂 Навігація

```powershell
# Поточна директорія
Get-Location

# Список файлів
Get-ChildItem
dir

# Перейти в папку
cd db_modules
cd ..

# Список модулів db_modules
Get-ChildItem db_modules\*.py
```

---

## 🧹 Очистка

```powershell
# Очистити консоль
Clear-Host
cls

# Видалити __pycache__
Remove-Item -Recurse -Force __pycache__
Remove-Item -Recurse -Force db_modules\__pycache__
```

---

## 📋 Швидкі Алаїси (Додай в $PROFILE)

```powershell
# Відкрити профіль PowerShell
notepad $PROFILE

# Додай ці алаїси:
function Start-Bot { .venv\Scripts\python.exe main.py }
Set-Alias bot Start-Bot

function Find-Function($name) {
    Select-String -Path "db.py.backup_before_cleanup" -Pattern "def $name\(" -Context 0,30
}
Set-Alias findf Find-Function

function Test-Import($func) {
    py -c "from db import $func; print('✅ $func OK')"
}
Set-Alias testi Test-Import

# Перезавантаж профіль
. $PROFILE

# Тепер можна:
bot                           # запустити бота
findf function_name           # знайти функцію
testi function_name           # тестувати import
```

---

## 🛠️ Корисні Функції PowerShell

```powershell
# Функція для пошуку та додавання функції
function Add-DbFunction {
    param([string]$FunctionName)
    
    Write-Host "🔍 Шукаю функцію: $FunctionName" -ForegroundColor Yellow
    
    $result = Select-String -Path "db.py.backup_before_cleanup" -Pattern "def $FunctionName\(" -Context 0,50
    
    if ($result) {
        Write-Host "✅ Знайдено в рядку $($result.LineNumber)" -ForegroundColor Green
        $result.Context.PostContext | ForEach-Object { Write-Host $_ }
    } else {
        Write-Host "❌ Функцію не знайдено" -ForegroundColor Red
    }
}

# Використання:
Add-DbFunction "get_player_stats"
```

---

## 🎯 Workflow Example (PowerShell)

```powershell
# 1. Запустити бота
.venv\Scripts\python.exe main.py

# 2. Помилка: ImportError: cannot import name 'missing_func'

# 3. Знайти функцію
Select-String -Path "db.py.backup_before_cleanup" -Pattern "def missing_func\(" -Context 0,30

# 4. Скопіювати код, додати в db_modules\module.py

# 5. Оновити __init__.py
code db_modules\__init__.py

# 6. Тестувати
py -c "from db import missing_func; print('✅')"

# 7. Повторити з кроку 1
```

---

## 🔗 Корисні Посилання

- PowerShell Docs: https://docs.microsoft.com/powershell/
- Select-String: https://docs.microsoft.com/powershell/module/microsoft.powershell.utility/select-string
- Python on Windows: https://docs.python.org/3/using/windows.html

---

**Створено:** 2026-08-17  
**Для:** Windows PowerShell
