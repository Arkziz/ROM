# ROM Stage 21.1.1 - інвентаризація та класифікація модулів V1

- **Canonical revision:** `Stage 21.1.1a`
- **Статус:** `GO`
- **Гілка:** `rewrite/rom-v2`
- **Python-модулів V1:** `999`
- **Syntax errors:** `0`

## Класифікація

- `REWRITE`: **179**
- `CONTENT_EXTRACT`: **41**
- `TEST_REFERENCE`: **724**
- `DO_NOT_MIGRATE`: **31**
- `NEEDS_MANUAL_REVIEW`: **24**

## Виправлення Stage 21.1.1a

- Слово `contract` більше не є самостійним test marker.
- `handlers/contracts.py` і `systems/contract_system.py` класифікуються як runtime `REWRITE`.
- Усі `__init__.py` класифікуються як `DO_NOT_MIGRATE`; V2 створить package boundaries та exports заново.
- Test classification дозволена лише для явних test directories, prefixes і suffixes.

## Черги наступних аудитів

- Duplicate definitions: **18**.
- Telegram + SQL coupling: **9**.
- Historical markers: **155**.
- Owner unresolved: **24**.

## Використання

- Цей Markdown і відповідний JSON після Stage 21.1.1a є canonical inventory.
- Класифікація є planning contract, а не дозволом механічно копіювати V1.
- Production DB/WAL/SHM не відкривалися й не змінювалися.

## Наступний етап

Stage 21.1.2 - AST-аудит повторних визначень, alias chains і runtime overrides.
