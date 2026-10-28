# Stage 21.16.1c — Independent development bot shell

## Result

The isolated ROM V2 development shell is connected through a pure Telegram HTTP transport. The transport performs request serialization and response validation only. It does not import persistence, repositories, Unit of Work, domain services, SQLite, or V1 runtime modules.

## Boundaries

- `rom_v2/infrastructure/telegram/bot_api.py`: HTTP transport only.
- `rom_v2/presentation/development_shell.py`: localized immutable shell views only.
- `rom_v2/app/development_bot.py`: composition, allowlist, update parsing, and lifecycle.
- Gameplay runtime and production persistence remain `NOT_CONNECTED`.
- No V1 import or fallback was added.

## Manual game check

REQUIRED after the patch succeeds:

1. Start the separate V2 development bot with the configured V2 token.
2. From an allowed account send `/start`; verify the ROM V2 development shell.
3. Press `Стан V2`; verify the honest `NOT_CONNECTED` markers.
4. Press `Назад`; verify return to the shell.
5. Send `/start` from an account outside the allowlist; verify no response.
6. Stop and start the V2 bot; verify clean shutdown and restart without starting V1.
