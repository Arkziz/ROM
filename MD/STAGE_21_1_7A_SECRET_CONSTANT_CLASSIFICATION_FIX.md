# ROM Stage 21.1.7a - secret constant classification fix

- **Статус:** `GO`
- **Secret-like constants before:** `6`
- **Secret-like constants after:** `0`
- **False positives removed:** `6`

## Root cause

Gameplay identifiers containing `TOKEN` were incorrectly treated as credential secrets.

## Corrected rule

Only credential-oriented names such as `BOT_TOKEN`, `ACCESS_TOKEN`, `AUTH_TOKEN`, `SECRET`, `PASSWORD`, `API_KEY`, `PRIVATE_KEY` and `CREDENTIAL` are classified as secret-like.

Production DB/WAL/SHM were not opened or modified.
