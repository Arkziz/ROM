# Stage 19.28.9: аудит sequencing повідомлень сюжетних квестів

**Рішення:** `MESSAGE_SEQUENCING_MUTATION_REQUIRED`

Read-only аудит ACCEPT/COMPLETE для квестів 1-50.

## Підсумок

- Перевірено 100 cases.
- Projected зайвих повідомлень: **73**.
- Cross-NPC completions: 1, 4, 5, 7, 8, 9, 10, 13, 16, 19, 20, 24, 26, 27, 32, 35, 38, 39, 41, 46, 47, 49.
- Story end: 50.

## Виявлені проблеми

### `DUPLICATE_ACCEPT_CONFIRMATION`

- Severity: **LOW**
- Scope: all 50 quests
- Причина: A generic acceptance receipt is immediately followed by a full ACTIVE card.

### `UNCONDITIONAL_POST_COMPLETION_NPC_REFRESH`

- Severity: **MEDIUM**
- Scope: cross-NPC handoffs and story end
- Причина: Every completion refreshes the current NPC, producing an empty card when the next giver differs or no next quest exists.

## Контракт наступного patch

1. ACCEPT: одна ACTIVE-картка з marker, без окремого generic receipt.
2. COMPLETE same NPC: receipt + next quest card.
3. COMPLETE cross-NPC: receipt із route, без empty current-NPC card.
4. STORY END: лише receipt.
5. Lifecycle, rewards, callbacks і DB не змінювати.
