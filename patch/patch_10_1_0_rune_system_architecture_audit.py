#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 10.1.0: install and run a read-only Rune System architecture audit."""
from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "10.1.0"
TOOL_NAME = "audit_rune_system_architecture.py"
REPORT_NAME = "RUNE_SYSTEM_10_1_0_ARCHITECTURE_AUDIT.md"

TOOL = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only architecture audit for ROM Rune System 10.x.

This tool does not alter gameplay files or database rows. It inspects the
current code, schema and item namespace, then produces a concrete architecture
plan for runes, Firius Tokens, sockets, fusion and extractors.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "game.db"
REPORT = ROOT / "RUNE_SYSTEM_10_1_0_ARCHITECTURE_AUDIT.md"

REQUIRED_FILES = (
    "db.py",
    "main.py",
    "keyboards.py",
    "handlers/daily.py",
    "handlers/inventory.py",
    "handlers/city.py",
    "handlers/dev.py",
    "handlers/auction_house.py",
    "systems/player_system.py",
    "systems/equipment_system.py",
    "systems/reward_system.py",
    "systems/refine_system.py",
    "systems/auction_house_system.py",
    "data/balance.py",
    "data/equipment_profiles.py",
    "migrations/runner.py",
)

RUNE_STATS = ("STR", "STA", "DEX", "INT", "WIS")
RUNE_LEVELS = (1, 2, 3, 4, 5)
RUNE_SLOT_LIMITS = {
    "main_hand": 2,
    "off_hand": 1,
    "helmet": 1,
    "shoulders": 1,
    "chest": 3,
    "gloves": 1,
    "legs": 2,
    "boots": 1,
    "necklace": 1,
    "ring": 1,
}
PROPOSED_ITEMS = {
    **{
        501 + stat_index * 5 + level_index: f"rune_{stat.lower()}_{level_index + 1}"
        for stat_index, stat in enumerate(RUNE_STATS)
        for level_index in range(5)
    },
    526: "firius_token",
    527: "rune_extractor",
    528: "rune_extractor_perfect",
}


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest(),
        path.stat().st_size,
        path.stat().st_mtime_ns,
    )


def read(rel):
    path = ROOT / rel
    return path.read_text(encoding="utf-8-sig")


def parse(rel):
    text = read(rel)
    return text, ast.parse(text, filename=str(ROOT / rel))


def function_info(rel, name):
    text, tree = parse(rel)
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    nodes.sort(key=lambda node: node.lineno)
    return [
        {
            "line": node.lineno,
            "end_line": node.end_lineno,
            "args": [argument.arg for argument in node.args.args],
            "source": ast.get_source_segment(text, node) or "",
        }
        for node in nodes
    ]


def function_names(rel):
    _text, tree = parse(rel)
    return sorted({
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    })


def table_columns(conn, table):
    quoted = '"' + table.replace('"', '""') + '"'
    return [row[1] for row in conn.execute(f"PRAGMA table_info({quoted})").fetchall()]


def logical_snapshot(conn):
    tables = [
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    result = {}
    for table in tables:
        quoted = '"' + table.replace('"', '""') + '"'
        columns = table_columns(conn, table)
        order = ", ".join(
            '"' + column.replace('"', '""') + '"' for column in columns
        ) or "rowid"
        rows = conn.execute(f"SELECT * FROM {quoted} ORDER BY {order}").fetchall()
        payload = json.dumps(
            [
                [value.hex() if isinstance(value, bytes) else value for value in row]
                for row in rows
            ],
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        result[table] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return result


def find_text_occurrences(patterns):
    findings = defaultdict(list)
    excluded = {".git", ".venv", "venv", "backup", "patch", "__pycache__"}
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if any(part in excluded for part in rel.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except Exception:
            continue
        for number, line in enumerate(lines, 1):
            lower = line.lower()
            for pattern in patterns:
                if pattern.lower() in lower:
                    findings[pattern].append(f"{rel.as_posix()}:{number}")
    return findings


def count_sql_mutations(source):
    upper = source.upper()
    return {
        keyword: upper.count(keyword)
        for keyword in ("INSERT ", "UPDATE ", "DELETE ", "COMMIT", "ROLLBACK")
    }


def main():
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"missing required file: {rel}")
    if not DB_PATH.is_file():
        fail("missing game.db")

    file_before = fingerprint(DB_PATH)
    conn = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        logical_before = logical_snapshot(conn)
        quick_check = conn.execute("PRAGMA quick_check").fetchone()[0]
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        schema = {
            table: table_columns(conn, table)
            for table in sorted(tables)
            if not table.startswith("sqlite_")
        }

        item_columns = schema.get("items", [])
        inventory_columns = schema.get("inventory", [])
        equipment_columns = schema.get("equipment_slots", [])
        user_columns = schema.get("users", [])
        item_rows = conn.execute(
            "SELECT id, name, type, category, max_stack "
            "FROM items ORDER BY id"
        ).fetchall() if "items" in tables else []
        used_item_ids = {int(row[0]) for row in item_rows}
        proposed_conflicts = [
            {
                "id": item_id,
                "proposed_type": item_type,
                "current": next(
                    (row for row in item_rows if int(row[0]) == item_id), None
                ),
            }
            for item_id, item_type in PROPOSED_ITEMS.items()
            if item_id in used_item_ids
        ]

        max_static_id = max(
            (item_id for item_id in used_item_ids if item_id < 1000000),
            default=0,
        )
        auction_tables = sorted(table for table in tables if "auction" in table)
        auction_columns = {
            table: schema.get(table, []) for table in auction_tables
        }
        logical_mid = logical_snapshot(conn)
    finally:
        conn.close()

    if logical_before != logical_mid:
        fail("logical database snapshot changed inside read-only connection")
    if quick_check != "ok":
        fail(f"database quick_check={quick_check}")

    seed_items = function_info("db.py", "seed_items")
    add_item = function_info("db.py", "add_item")
    consume_by_id = function_info("db.py", "consume_user_item_by_item_id")
    daily_claim_db = function_info("db.py", "claim_daily_quest_reward")
    daily_claim_system = function_info("systems/reward_system.py", "claim_daily_quest_reward")
    player_stats = function_info("systems/player_system.py", "get_player_stats")
    item_bonuses = function_info("systems/equipment_system.py", "get_item_bonuses")
    all_equipped = function_info("systems/equipment_system.py", "get_all_equipped_items")
    auction_snapshot = function_info(
        "systems/auction_house_system.py", "get_inventory_item_snapshot_for_auction"
    )
    auction_buy = function_info("systems/auction_house_system.py", "buy_auction_lot_v2")
    city_functions = function_names("handlers/city.py")
    dev_functions = function_names("handlers/dev.py")
    inventory_functions = function_names("handlers/inventory.py")

    occurrences = find_text_occurrences((
        "rune_slots",
        "socket",
        "firius",
        "жетон фіріуса",
        "rune_system",
        "installed_rune",
        "refine_level",
        "claim_daily_quest_reward",
        "craft",
    ))

    existing_rune_named_items = [
        row for row in item_rows
        if "rune" in str(row[2] or "").lower()
        or "руна" in str(row[1] or "").lower()
    ]

    daily_source = "\n".join(
        item["source"] for item in daily_claim_system + daily_claim_db
    )
    daily_mutations = count_sql_mutations(daily_source)

    # Architectural decisions.
    rune_table = {
        "name": "inventory_runes",
        "columns": (
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "inventory_id INTEGER NOT NULL",
            "slot_index INTEGER NOT NULL",
            "rune_item_id INTEGER NOT NULL",
            "rune_stat TEXT NOT NULL",
            "rune_level INTEGER NOT NULL",
            "inserted_at TEXT NOT NULL",
            "UNIQUE(inventory_id, slot_index)",
            "FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE",
        ),
    }
    reasons_for_table = [
        "Руни належать конкретному inventory-екземпляру, а не шаблону items.",
        "Нормалізовані рядки простіше перевіряти, індексувати й переносити в Auction snapshot.",
        "JSON-поле у inventory ускладнить точкові constraints, пошук, міграції та атомарне вилучення.",
        "UNIQUE(inventory_id, slot_index) фізично забороняє дві руни в одному слоті.",
        "Каскадне видалення очищає sockets при законному знищенні equipment; extraction спершу повертає руни, потім видаляє предмет у транзакції.",
    ]

    slot_total = sum(RUNE_SLOT_LIMITS.values())
    expected_rune_items = len(RUNE_STATS) * len(RUNE_LEVELS)

    report = [
        "# ROM 10.1.0 — Аудит архітектури системи рун",
        "",
        f"Згенеровано: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Підсумкове рішення",
        "",
        "**Систему рун можна впроваджувати на поточному baseline 9.0.13o без попереднього рефакторингу.**",
        "",
        "Рекомендована архітектура: окремий `systems/rune_system.py`, канонічні rune constants у `data/runes.py`, нормалізована таблиця `inventory_runes`, stackable rune/token/extractor items у `items` та `inventory`, UI через `handlers/runes.py`, а `db.py` залишається тонким compatibility facade.",
        "",
        "## Безпека аудиту",
        "",
        "- Gameplay-файли змінено: **0**",
        "- Рядки реальної БД змінено: **0**",
        f"- SQLite `PRAGMA quick_check`: **{quick_check}**",
        f"- Логічний snapshot БД незмінний: **{logical_before == logical_mid}**",
        f"- SHA/size/mtime файла БД незмінні: **{file_before == fingerprint(DB_PATH)}**",
        "- БД відкрито через `mode=ro` та `PRAGMA query_only=ON`.",
        "",
        "## Затверджені бізнес-правила",
        "",
        f"- Характеристики: `{list(RUNE_STATS)}`.",
        f"- Рівні: `{list(RUNE_LEVELS)}`; бонус дорівнює рівню, тобто I=+1 … V=+5.",
        f"- Кількість rune item definitions: **{expected_rune_items}**.",
        f"- Rune slot map: `{RUNE_SLOT_LIMITS}`.",
        f"- Загальна кількість слотів на повному комплекті: **{slot_total}**.",
        "- Fusion: `3 однакові руни того самого stat/level + 1 Жетон Фіріуса → 1 руна наступного рівня`.",
        "- Fusion success: **100%**.",
        "- Rune V не може бути fusion source.",
        "- Жорсткого денного fusion-ліміту немає.",
        "- За успішний claim щоденного завдання: **10 Жетонів Фіріуса**.",
        "- Жетони накопичуються і не мають daily reset.",
        "- Один успішний fusion витрачає рівно 1 жетон.",
        "- Простий екстрактор повертає одну випадкову вставлену руну та знищує equipment.",
        "- Досконалий екстрактор повертає всі вставлені руни та знищує equipment.",
        "",
        "## Поточна схема, важлива для рун",
        "",
        f"- `items` columns: `{item_columns}`",
        f"- `inventory` columns: `{inventory_columns}`",
        f"- `equipment_slots` columns: `{equipment_columns}`",
        f"- `users` columns relevant to stats/progression: `{[column for column in user_columns if column in {'user_id','str','sta','dex','int','wis','hp','max_hp','mp','max_mp','level','current_location'}]}`",
        "",
        "### Висновок щодо зберігання",
        "",
        f"Рекомендована таблиця: `{rune_table['name']}`.",
        "",
        "```text",
        *rune_table["columns"],
        "```",
        "",
    ]
    report.extend(f"- {reason}" for reason in reasons_for_table)
    report.extend([
        "",
        "Не рекомендується додавати `rune_slots` JSON у `items`, оскільки кількість слотів є правилом `slot_key`, а не властивістю кожного generated item template. Не рекомендується зберігати вставлені руни в `items`, бо generated item може мати власника, Auction snapshot і окремий inventory lifecycle.",
        "",
        "## Запропонований namespace предметів",
        "",
        "Запропоновано зарезервувати безперервний діапазон `501–528`:",
        "",
        "- `501–525`: 25 рун, п’ять stats × п’ять рівнів.",
        "- `526`: `firius_token`.",
        "- `527`: `rune_extractor`.",
        "- `528`: `rune_extractor_perfect`.",
        "",
        f"- Конфлікти запропонованих ID у поточній БД: `{proposed_conflicts}`",
        f"- Найбільший поточний статичний item ID: `{max_static_id}`",
        f"- Поточні предмети з rune-подібними назвами/типами: `{existing_rune_named_items}`",
        "",
        "Якщо `proposed_conflicts` порожній, 10.2.0 може офіційно закріпити цей namespace. ID 402, Руна Успіху, залишається матеріалом заточки й не належить новій socket-rune системі.",
        "",
        "## Нагорода щоденного завдання",
        "",
        f"- `db.py.claim_daily_quest_reward` definitions: `{[(item['line'], item['args']) for item in daily_claim_db]}`",
        f"- `systems.reward_system.claim_daily_quest_reward` definitions: `{[(item['line'], item['args']) for item in daily_claim_system]}`",
        f"- Mutation markers у claim flow: `{daily_mutations}`",
        "",
        "Жетони слід додавати лише всередині успішної транзакції claim, після перевірки completed/reward_claimed та перед commit. Якщо додавання жетонів не може завершитися через capacity або іншу помилку, вся нагорода має rollback. Повторний claim не повинен видавати жетони.",
        "",
        "## Інтеграція зі статами",
        "",
        f"- `systems.player_system.get_player_stats`: `{[(item['line'], item['args']) for item in player_stats]}`",
        f"- `systems.equipment_system.get_item_bonuses`: `{[(item['line'], item['args']) for item in item_bonuses]}`",
        f"- `systems.equipment_system.get_all_equipped_items`: `{[(item['line'], item['args']) for item in all_equipped]}`",
        "",
        "Рекомендована точка інтеграції: `rune_system.get_equipped_rune_stat_totals(user_id)` повертає dict `{str, sta, dex, int, wis}`. `player_system.get_player_stats()` додає цей dict один раз після equipment bonuses. Це автоматично впливає на ATK, magic ATK, Max HP, PDEF, MDEF, crit, MP та regen через наявні похідні формули.",
        "",
        "Після вставки або вилучення руни STA/WIS/INT потрібно викликати наявні sync helpers Max HP/MP. Current HP/MP clamp до нового максимуму, але вставка не повинна безкоштовно лікувати до повного.",
        "",
        "## Інтеграція з Auction House",
        "",
        f"- Auction tables: `{auction_tables}`",
        f"- Auction columns: `{auction_columns}`",
        f"- Snapshot function: `{[(item['line'], item['args']) for item in auction_snapshot]}`",
        f"- Buy function: `{[(item['line'], item['args']) for item in auction_buy]}`",
        "",
        "Auction snapshot має отримати `runes_snapshot` як стабільний JSON-масив або окремі snapshot rows. Для поточної архітектури найменш ризиковий варіант: JSON у lot snapshot, бо Auction уже заморожує item instance. Під час listing живі `inventory_runes` мають бути перенесені/зарезервовані разом з item; під час cancel/expire/buy вони відновлюються для нового inventory instance. Лот не повинен залежати від видаленого seller inventory_id.",
        "",
        "Rune items і Жетони Фіріуса можна продавати як stack items лише після окремого рішення. На першому етапі рекомендується заборонити Auction для жетонів та екстракторів; rune items дозволити пізніше окремим балансним патчем.",
        "",
        "## Рунний Майстер і UI",
        "",
        f"- City top-level functions: `{city_functions}`",
        f"- Inventory top-level functions: `{inventory_functions}`",
        f"- DEV top-level functions: `{dev_functions}`",
        "",
        "Рекомендовані нові файли:",
        "",
        "- `data/runes.py`: stats, levels, item IDs, names, bonuses, slot limits, token/extractor IDs.",
        "- `systems/rune_system.py`: schema, reads, insertion, fusion, extraction, stat totals, transactions.",
        "- `handlers/runes.py`: Рунний Майстер, callback state machine, підтвердження та UI.",
        "- `tools/smoke_test_rune_*.py`: ізольовані contracts.",
        "",
        "Рунного Майстра слід додати в уже реалізований Ремісничий квартал, без створення паралельного меню. Callback namespace: `rune:*`, з короткими payload та server-side повторною перевіркою ownership/state.",
        "",
        "## Атомарні операції",
        "",
        "### Вставка",
        "",
        "1. `BEGIN IMMEDIATE`.",
        "2. Перевірити ownership equipment inventory_id та що item є equipment.",
        "3. Заборонити preview/Auction-reserved/відсутній item.",
        "4. Визначити slot limit за `slot_key`.",
        "5. Перевірити вільний socket index.",
        "6. Перевірити ownership rune stack і валідність rune item.",
        "7. Списати 1 rune item.",
        "8. Додати `inventory_runes` row.",
        "9. Commit; після commit синхронізувати похідні HP/MP.",
        "",
        "### Fusion",
        "",
        "1. `BEGIN IMMEDIATE`.",
        "2. Перевірити rune level < V.",
        "3. Перерахувати 3 rune items та 1 token без довіри до callback.",
        "4. Перевірити capacity для result stack з урахуванням того, що source stacks зменшаться.",
        "5. Списати 3 руни та 1 token.",
        "6. Додати 1 rune наступного рівня.",
        "7. Commit. При будь-якій помилці rollback без часткового списання.",
        "",
        "### Extraction",
        "",
        "1. Заборонити extraction equipped item до явного unequip або виконати контрольоване unequip у транзакції. Рекомендація: вимагати, щоб предмет був знятий.",
        "2. Перевірити ownership, rune count, extractor та bag capacity.",
        "3. Простий: cryptographically не потрібно, достатньо `random.choice`, повернути одну rune item.",
        "4. Досконалий: повернути всі rune items.",
        "5. Списати 1 extractor.",
        "6. Видалити equipment inventory row; CASCADE видалить socket rows.",
        "7. Commit; rollback при будь-якій помилці.",
        "",
        "## Взаємодія із заточкою, ремонтом і продажем",
        "",
        "- `refine_level` та руни незалежні й належать одному inventory instance.",
        "- Вставка/вилучення не змінює refine level, durability, rarity або item level.",
        "- Durability=0 вимикає весь equipment contribution, включно з rune bonuses, бо предмет не дає бонусів.",
        "- Trader sale та item deletion повинні каскадно видаляти socket rows; продаж предмета з рунами має бути заблокований або вимагати явне підтвердження втрати рун. Рекомендація 10.x: блокувати звичайний продаж предметів із рунами.",
        "- Repair cost не залежить від рун.",
        "- Rune slot count залежить лише від equipment slot_key, а не rarity або refine level.",
        "",
        "## Міграційна стратегія",
        "",
        "10.2.0 має створити `data/runes.py`, `systems/rune_system.py`, таблицю `inventory_runes`, індекси та seed items 501–528 через versioned migration/explicit init. Існуючі inventory rows не потребують backfill: відсутність rows означає 0 вставлених рун.",
        "",
        "Рекомендовані індекси:",
        "",
        "```text",
        "UNIQUE inventory_runes(inventory_id, slot_index)",
        "INDEX inventory_runes_inventory_id(inventory_id)",
        "INDEX inventory_runes_rune_item_id(rune_item_id)",
        "```",
        "",
        "## Виявлені точки та залишкові назви",
        "",
    ])
    for pattern, hits in sorted(occurrences.items()):
        report.append(f"- `{pattern}`: `{hits}`")
    report.extend([
        "",
        "`Руна Успіху` у Refine System є окремим матеріалом. Назви нових socket runes повинні мати item types на кшталт `rune_str_1`, щоб не конфліктувати з `success_rune`.",
        "",
        "## План smoke-тестів",
        "",
        "- Schema init idempotency та відсутність змін existing equipment.",
        "- 25 rune definitions, token, два extractors, унікальні IDs/types.",
        "- Stack add/consume для rune/token items.",
        "- Slot limits для всіх 10 equipment slots, загалом 14.",
        "- Ownership, forged callback, full sockets, non-equipment rejection.",
        "- Stat totals тільки з equipped, unbroken equipment.",
        "- STA/INT/WIS sync для Max HP/MP без безкоштовного full heal.",
        "- Fusion exact 3+1→1, level V rejection, insufficient source/token, rollback.",
        "- Daily claim видає рівно 10 tokens один раз.",
        "- Simple extractor повертає рівно одну rune, знищує item/extractor.",
        "- Perfect extractor повертає всі runes, знищує item/extractor.",
        "- Auction listing/buy/cancel/expire з rune snapshot без втрат/дублів.",
        "- Trader protection для socketed equipment.",
        "- Existing Refine, Equipment, Character, Player Stats, Daily, Auction contracts залишаються green.",
        "- Logical real-DB snapshot незмінний для read-only audits.",
        "",
        "## Ризики",
        "",
        "1. **Auction inventory_id lifecycle:** високий ризик втрати socket rows, якщо snapshot не розширити до дозволу listing socketed items.",
        "2. **Подвійне нарахування stats:** rune totals слід додавати лише в одному canonical місці.",
        "3. **HP/MP synchronization:** зменшення rune bonuses має clamp current values без heal-to-full.",
        "4. **Bag capacity:** fusion/extraction повинні рахувати майбутні stack slots всередині транзакції.",
        "5. **Item ID namespace:** 501–528 треба остаточно перевіряти при кожному seed/migration і не використовувати повторно.",
        "6. **Назва «руна»:** не змішувати socket runes з Refine `success_rune` ID 402.",
        "7. **Concurrency:** усі mutation flows виконувати через `BEGIN IMMEDIATE` та повторну перевірку стану.",
        "",
        "## Рекомендована послідовність версії 10",
        "",
        "1. `patch_10_2_0_rune_and_firius_token_data_model.py`",
        "2. `patch_10_3_0_daily_quest_firius_token_reward.py`",
        "3. `patch_10_4_0_rune_inventory_items_and_dev_commands.py`",
        "4. `patch_10_5_0_equipment_rune_slots.py`",
        "5. `patch_10_6_0_rune_master_and_insertion.py`",
        "6. `patch_10_7_0_rune_character_stat_bonuses.py`",
        "7. `patch_10_8_0_rune_fusion_with_firius_tokens.py`",
        "8. `patch_10_9_0_simple_rune_extractor.py`",
        "9. `patch_10_10_0_perfect_rune_extractor.py`",
        "10. `patch_10_11_0_rune_drops_and_balance.py`",
        "11. `patch_10_12_0_rune_system_final_closure_audit.py`",
        "",
        "## Висновок",
        "",
        "Першим mutation-патчем має бути 10.2.0. Він повинен створити лише фундамент: canonical data, schema, seed items, read APIs та tests. Daily reward, sockets UI, stat effects, fusion, extraction, drops та Auction support слід підключати окремими версіями, щоб кожен ризик був ізольований і мав rollback.",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] Rune System architecture audit")
    print(f"- proposed rune items: {expected_rune_items}")
    print(f"- proposed utility items: {len(PROPOSED_ITEMS) - expected_rune_items}")
    print(f"- proposed item ID conflicts: {len(proposed_conflicts)}")
    print(f"- equipment rune slots total: {slot_total}")
    print("- storage decision: normalized inventory_runes table")
    print("- daily fusion counter required: no")
    print("- Firius Tokens per successful daily claim: 10")
    print("- fusion cost: 3 runes + 1 token")
    print("- Auction snapshot extension required: yes")
    print("- gameplay mutations: 0")
    print("- real database mutations: 0")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
'''


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    candidates = (here.parent.parent, Path.cwd(), Path.cwd().parent)
    for root in candidates:
        root = root.resolve()
        if (
            (root / "db.py").is_file()
            and (root / "main.py").is_file()
            and (root / "game.db").is_file()
            and (root / "systems" / "equipment_system.py").is_file()
            and (root / "systems" / "auction_house_system.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM або обов'язкові файли проєкту.")


def main():
    root = find_root()
    target = root / "tools" / TOOL_NAME
    backup = None

    if target.exists() and target.read_text(encoding="utf-8-sig") != TOOL:
        backup_dir = root / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backup_dir / f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(target, backup)

    target.write_text(TOOL, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        py_compile.compile(str(target), doraise=True)
        result = subprocess.run(
            [sys.executable, str(target)],
            cwd=root,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"audit exit code {result.returncode}")
    except Exception as exc:
        if backup is not None:
            shutil.copy2(backup, target)
        elif target.exists():
            target.unlink()
        fail(f"Аудит не пройдено; audit tool відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Створено: tools/{TOOL_NAME}")
    print(f"✅ Створено: {REPORT_NAME}")
    print("✅ Gameplay-код і реальна game.db не змінені.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root) if backup else 'не потрібні - новий файл'}")
    print("Повторний запуск:")
    print(f"   python ./tools/{TOOL_NAME}")


if __name__ == "__main__":
    main()
