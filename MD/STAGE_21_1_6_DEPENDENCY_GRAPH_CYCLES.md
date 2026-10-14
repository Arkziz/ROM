# ROM Stage 21.1.6 - dependency graph, cycles і V2 directions

- **Статус:** `GO`
- **Nodes:** `244`
- **Internal edges:** `639`
- **Strongly connected cycles:** `5`
- **Forbidden-direction candidates:** `32`
- **Orphan modules:** `19`

## Review queues

- Cycles: **5**
- Forbidden directions: **32**
- High fan-in: **15**
- High fan-out: **13**
- Orphans: **19**

## V2 dependency contract

- `domain` залежить тільки від стандартної бібліотеки та власних domain modules.
- `application` залежить від domain і application ports.
- `infrastructure` залежить від domain/application ports, але не навпаки.
- Telegram adapters не імпортуються domain, application або persistence.
- Content не залежить від runtime handlers, systems або persistence.
- Composition root є єдиним місцем wiring concrete infrastructure.
- Цикли V1 не копіюються; для кожного визначається owner, port або extracted service.
- Production DB/WAL/SHM не відкривалися і не змінювалися.

## Наступний етап

Stage 21.1.7 - inventory configuration, environment variables і external integrations.
