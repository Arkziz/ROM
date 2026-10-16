# Stage 21.3.1 — Isolated ROM V2 package skeleton

- **Status:** `IMPLEMENTED`
- **Entrypoint:** `python -m rom_v2.main`
- **Gameplay:** `DISABLED`
- **V1 runtime imports:** `FORBIDDEN`

## Created structure

```text
rom_v2/
  domain/
  application/
  infrastructure/
  app/
  content/
  config.py
  container.py
  lifecycle.py
  bootstrap.py
  main.py
tests_v2/
  test_v2_bootstrap_smoke.py
```

## Bootstrap behavior

The entrypoint builds an explicit container, validates safe bootstrap configuration, starts and stops lifecycle, and prints one JSON smoke record. It does not start Telegram, open a database, start background jobs, or execute gameplay.

## Smoke result

```json
{
  "application": "rom_v2",
  "background_jobs_started": false,
  "database_opened": false,
  "gameplay_enabled": false,
  "mode": "bootstrap",
  "status": "ready",
  "telegram_started": false
}
```

## Verifiers

- `dependency`: `PASS`
- `structure`: `PASS`
- `result`: `PASS`
- `events`: `PASS`
- `uow`: `PASS`
- `clock_rng`: `PASS`
- `code_comments`: `PASS`

## Next roadmap stage

Stage 21.3.2 — Runtime directories and Git exclusion.
