# Stage 21.14.5b — About, useful links and support parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Production mutation: **NO**
- `.env` opened: **NO**
- Production SQLite opened: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Resolved contract

### about_content
- Status: **RESOLVED**
- Contract: About content is canonical source-owned structured content. V2 must preserve confirmed section identity, ordering, titles and bodies without inventing or rewriting lore.
- Owners: `data/about_game.py`, `handlers/about_game.py`

### configuration
- Status: **RESOLVED**
- Contract: GAME_CHAT_URL, NEWS_CHANNEL_URL and SUPPORT_URL remain optional configuration keys. Runtime values are external configuration and must not be copied from .env into source, reports or defaults.
- Owners: `config.py`, `.env at runtime only`

### url_validation
- Status: **RESOLVED**
- Contract: Configured public link buttons use fail-closed HTTPS validation. Missing, blank, malformed or non-HTTPS values are treated as unavailable rather than rendered.
- Owners: `V1 URL validation/configuration path`

### useful_links_visibility
- Status: **RESOLVED**
- Contract: Useful-links navigation exposes only individually configured valid links. One unavailable link does not authorize a placeholder, guessed URL or fallback transport.
- Owners: `V1 account/useful-links keyboard path`

### support
- Status: **RESOLVED**
- Contract: Support is an optional validated external URL button. Provider name, destination and payment details are configuration data, not domain defaults; no payment flow or ledger mutation is added.
- Owners: `SUPPORT_URL configuration and account menu`

### navigation
- Status: **RESOLVED**
- Contract: About and useful-links screens return to the canonical account menu. Callback and row layout must be copied only from confirmed V1 presentation evidence during adapter integration.
- Owners: `handlers/about_game.py`, `account menu owner`

### runtime_boundary
- Status: **RESOLVED**
- Contract: Stage 21.14.5c may implement API-ready content/configuration/validation models only. Telegram handlers, environment loading, runtime registration and production persistence remain disconnected.
- Owners: `Stage 21 V2 architecture boundary`

## Explicit prohibitions

- Do not read or commit .env values.
- Do not invent About sections or lore.
- Do not hard-code chat, channel, support or payment destinations.
- Do not permit HTTP, Telegram usernames or arbitrary text as URL fallbacks unless separately evidenced and authorized.
- Do not add Telegram/runtime wiring or production persistence in Stage 21.14.5c.
- Do not manipulate game.db-wal or game.db-shm.

## Authorization

Stage 21.14.5c may implement only API-ready content, optional configuration descriptors, HTTPS fail-closed validation and visibility/navigation models within this contract. Runtime and Telegram integration remain out of scope.
