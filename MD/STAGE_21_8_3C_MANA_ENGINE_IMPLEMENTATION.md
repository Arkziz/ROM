# Stage 21.8.1b — Battle Aggregate implementation

- Status: **PASS**
- Evidence: **API_READY**
- Runtime/Telegram: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented one canonical V2 Mana Engine for future PvE, PvP and simulator consumers. It owns Max MP, half-up skill costs, validation-before-debit, clamped restore, passive regeneration, post-combat floor and max-change clamping. Persistence and presentation remain external.
