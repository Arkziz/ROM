# Stage 21.4.2 — Test account allowlist

- **Status:** `NOT_REQUIRED`
- **Decision type:** policy-only closure
- **Production allowlist path created:** `False`

## Rationale

The development bot is privately operated and is not intended for publication or group use. A static account allowlist would add recurring administration and would require configuration changes whenever another owner-controlled test account is added.

## Accepted risk

Knowledge of the bot token is not required to contact a Telegram bot. If the development bot username becomes known, a third party could send updates to the bot while no account-level allowlist is enforced.

## Guardrails

- Do not publish the development bot username.
- Do not add the development bot to groups or channels.
- Do not reuse the development token for production.
- Do not add hard-coded Telegram user IDs to production code.
- If access control becomes necessary, implement it as a separate future stage using local configuration rather than hard-coded IDs.

## Explicit non-implementation

No allowlist module, user-ID list, database table, environment variable, Telegram request, polling process, or alternate production path is introduced by this stage.

## Next stage

Stage 21.4.3 — Telegram adapter skeleton.
