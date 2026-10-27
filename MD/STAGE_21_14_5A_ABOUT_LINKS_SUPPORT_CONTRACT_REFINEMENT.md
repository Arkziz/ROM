# Stage 21.14.5a — About, useful links and support contract refinement

- Status: **PASS**
- Decision: **REFINED_CONTRACT_READY_FOR_PARITY_RESOLUTION**
- Next action: **GO_TO_PARITY_RESOLUTION**
- Production mutation: **NO**
- `.env` opened: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Refined contract

### about_content
- Status: **REFINED**
- About content remains canonical source-owned ordered sections. V2 may model and navigate confirmed sections but must not rewrite, summarize, reorder or invent lore/content during this stage.

### useful_links
- Status: **REFINED**
- Useful links are optional configuration-backed entries for the game chat and news channel. An absent or invalid entry is hidden rather than rendered as a broken button.

### support
- Status: **REFINED**
- Support is one optional configuration-backed HTTPS URL entry. Provider, destination and payment semantics stay external configuration and are not embedded into the V2 domain.

### validation
- Status: **REFINED**
- Configured external links are accepted only as absolute HTTPS URLs with a non-empty network location; malformed, relative and non-HTTPS values fail closed and remain hidden.

### configuration
- Status: **REFINED**
- Domain input uses the three confirmed configuration names GAME_CHAT_URL, NEWS_CHANNEL_URL and SUPPORT_URL. The .env file and runtime secret values are not read, copied or persisted by the domain contract.

### navigation
- Status: **REFINED**
- About sections support deterministic section selection plus return to canonical account menu. Useful-links entry belongs beside About in the account-menu presentation, while callback identifiers and Telegram keyboards remain adapter concerns.

### availability
- Status: **REFINED**
- About remains available from canonical account navigation. Useful-links/support visibility is derived from validated configured entries and does not require database state.

## Unresolved evidence for parity resolution

- `https_validator_owner`: HTTPS validation marker was not confirmed in the selected owners; parity resolution must identify the exact V1 validator.

## Explicit prohibitions

- Do not invent or modify About text or section order.
- Do not hard-code runtime URL values, provider names or payment destinations.
- Do not read or copy .env values.
- Do not add Telegram handlers, callback IDs, runtime wiring or production persistence in refinement.
- Do not manipulate game.db-wal or game.db-shm.

This refinement does not authorize implementation. Stage 21.14.5b must resolve parity and explicitly authorize or reject implementation.
