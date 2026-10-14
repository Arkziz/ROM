# ROM Stage 21.1.3 - карта runtime handler і callback registration

- **Canonical revision:** `Stage 21.1.3a`
- **Статус:** `GO`
- **Registration modules:** `36`
- **Physical registration sites:** `377`
- **Main registration calls:** `32`
- **Route collision candidates:** `27`

## Виправлення Stage 21.1.3a

- Один decorator або explicit register call відповідає одному physical registration site.
- Decorator більше не дублюється як запис вкладеної функції та запис outer register function.
- Collision candidates перераховано лише за унікальними physical sites.
- Порядок `main.py` перенумеровано після сортування за номером рядка.

## Черги

- Modules with duplicate register definitions: **10**
- Route collision candidates: **27**
- Direct registry mutations: **0**

## Контракт V2

- Один composition root реєструє handlers у явному порядку.
- Domain та application layers не імпортують Telegram SDK.
- Callback namespaces мають одного owner.
- Route collision candidate потребує owner/precedence рішення, але не є автоматично підтвердженим runtime collision.
- Production DB/WAL/SHM не відкривалися і не змінювалися.

## Наступний етап

Stage 21.1.4 - inventory database access paths і transaction boundaries.
