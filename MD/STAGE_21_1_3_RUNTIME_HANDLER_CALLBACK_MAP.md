# ROM Stage 21.1.3 - карта runtime handler і callback registration

- **Статус:** `GO`
- **Registration modules:** `36`
- **Registration records:** `749`
- **Main registration calls:** `32`
- **Potential duplicate route groups:** `340`

## Черги

- Modules with duplicate register definitions: **10**
- Route collision candidates: **340**
- Direct registry mutations: **0**

## Контракт V2

- Один composition root реєструє handlers у явному порядку.
- Domain та application layers не імпортують Telegram SDK.
- Callback namespaces мають єдиного owner і не залежать від випадкового порядку декораторів.
- Direct mutation внутрішніх handler lists не переноситься.
- Повний список registration records, main order і collision candidates міститься у JSON.
- Production DB/WAL/SHM не відкривалися і не змінювалися.

## Наступний етап

Stage 21.1.4 - повний inventory database access paths і transaction boundaries.
