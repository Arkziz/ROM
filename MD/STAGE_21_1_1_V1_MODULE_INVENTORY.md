# ROM Stage 21.1.1 - інвентаризація та класифікація модулів V1

- **Статус:** `GO`
- **Гілка:** `rewrite/rom-v2`
- **Parent commit:** `b544f2429a1b80e8e3bab1aa05246367f1bc3fab`
- **Python-модулів V1:** `999`
- **Non-Python content records:** `0`
- **Syntax errors:** `0`

## Класифікація

- `REWRITE`: **266**
- `CONTENT_EXTRACT`: **43**
- `TEST_REFERENCE`: **636**
- `DO_NOT_MIGRATE`: **24**
- `NEEDS_MANUAL_REVIEW`: **30**

## Значення категорій

- `REWRITE`: поведінку відтворити через чисті V2 domain/application/infrastructure boundaries; код V1 не імпортувати.
- `CONTENT_EXTRACT`: витягнути лише accepted data/content, пропустити через schema validation і canonical content loader.
- `TEST_REFERENCE`: використати для fixtures, parity та acceptance, але не як production runtime.
- `DO_NOT_MIGRATE`: історичні migrations, порожні package markers або інші артефакти, які V2 створює заново.
- `NEEDS_MANUAL_REVIEW`: effective owner або accepted behavior неможливо безпечно визначити лише статично.

## Черги подальшого аудиту

- Повторні top-level definitions: **18** модулів.
- Telegram + SQL coupling: **9** модулів.
- Historical/compatibility markers: **155** модулів.
- Unresolved owner: **30** модулів.

## Правила використання

- Класифікація є planning contract, а не дозволом механічно копіювати файл.
- Будь-який `NEEDS_MANUAL_REVIEW` має пройти окремий owner/runtime audit до реалізації V2.
- Уся деталізація по кожному модулю, SHA-256, imports, дублікати, markers, inbound importers і рекомендований destination містяться у JSON.
- Production `game.db`, `game.db-wal` і `game.db-shm` не відкривалися та не змінювалися.

## Наступний етап

Stage 21.1.2 - AST-аудит повторних визначень, alias chains і runtime overrides.
