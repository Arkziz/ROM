# ROM Stage 21.0.3 - baseline ROM V1

- **Статус:** `GO`
- **Гілка:** `rewrite/rom-v2`
- **Parent commit:** `2ba3cbb3aa25f196cb740df093dcfd0c397d25c2`
- **Production-файлів:** `514`
- **Python-модулів:** `275`
- **Міграційних файлів:** `22`
- **Verifier/test-файлів:** `636`
- **Таблиць БД:** `52`

## Перевірки

| ID | Статус | Blocking | Результат |
|---|---:|---:|---|
| `TARGET_BRANCH` | **PASS** | ні | Active branch is rewrite/rom-v2. |
| `EXPECTED_PARENT` | **PASS** | ні | HEAD matches accepted Stage 21.0.2 commit. |
| `UPSTREAM` | **PASS** | ні | Rewrite branch upstream is configured and synchronized. |
| `WORKTREE` | **PASS** | ні | Working tree has no unexpected or pre-staged changes. |
| `PYTHON_SYNTAX` | **PASS** | ні | All tracked production Python modules parse successfully. |
| `PRODUCTION_INVENTORY` | **PASS** | ні | Captured 514 production files. |
| `MIGRATION_INVENTORY` | **PASS** | ні | Captured 22 migration files. |
| `VERIFIER_INVENTORY` | **PASS** | ні | Captured 636 verifier/test files. |
| `DATABASE_SCHEMA` | **PASS** | ні | Database schema captured safely and production bytes are unchanged. |

## Зафіксовані категорії

- Повний SHA-256 inventory tracked production і support files міститься у JSON.
- Python AST inventory містить imports, environment variable names, top-level functions/classes і повторні top-level symbols.
- Database schema зібрана тільки з isolated snapshot і містить tables, columns, foreign keys, indexes, triggers та views.
- Окремо зафіксовані migrations, dependencies, tools/verifiers і content packages.
- Файли з legacy/compat/candidate/shadow/deprecated/superseded/fallback markers позначено `REFERENCE_REVIEW_REQUIRED`.

## Правило використання baseline

- V1 є джерелом підтвердженої поведінки, контенту та parity fixtures.
- V1 runtime modules не можна імпортувати у майбутній `rom_v2` production runtime.
- Позначені reference-файли не переносяться механічно; authoritative owner визначається окремим контрактним аудитом Stage 21.1.
- Старі Stage 19-20 MD/JSON не відновлюються у робоче дерево; Git history залишається джерелом історичних артефактів.

## SQLite safety

- Production `game.db` не відкривалася через SQLite.
- `quick_check` і schema inventory виконано на isolated snapshot.
- `game.db-wal` і `game.db-shm` не видалялися, не очищувалися та не використовувалися для rollback.
- Побайтова незмінність production DB/WAL/SHM: `True`.

## Наступний етап

Stage 21.0.4 - створення анотованого Git tag фінального baseline Stage 20/V1.
