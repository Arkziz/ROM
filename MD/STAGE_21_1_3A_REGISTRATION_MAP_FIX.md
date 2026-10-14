# ROM Stage 21.1.3a - виправлення double counting registration map

- **Статус:** `GO`
- **Записів до виправлення:** `749`
- **Унікальних physical sites після виправлення:** `377`
- **Видалено дубльованих derived records:** `372`
- **Collision groups до виправлення:** `340`
- **Collision candidates після виправлення:** `27`

## Root cause

Stage 21.1.3 проходив `ast.walk()` outer register function і окремо обробляв decorator nested handler. Один physical decorator отримував два records із тим самим module, line, kind і call.

## Рішення

- Decorators збираються тільки з decorated function node.
- Explicit `register_*_handler` calls збираються окремим проходом.
- Deduplication виконується за physical site key: module, line, column, kind.
- Canonical Stage 21.1.3 JSON та Markdown замінені виправленою revision.

## Наступний етап

Stage 21.1.4 - inventory database access paths і transaction boundaries.
