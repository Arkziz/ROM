# Stage 21.15.1d - Flat domain remediation

## Result

Five recently introduced nested domain packages are consolidated into the established flat `rom_v2/domain/*.py` layout:

- `events.py`
- `inactivity_reminders.py`
- `ratings_history_chronicles.py`
- `about_links_support.py`
- `dev_authorization.py`

Their unit tests are moved to flat `tests_v2/test_*.py` modules. Existing executable checks are updated to the new test module paths. The nested package and nested unit-test directories are removed.

This is structural remediation only. Runtime, Telegram and production persistence are not connected. Production SQLite and `.env` are not opened. `game.db-wal` and `game.db-shm` are not manipulated. Manual in-game verification is not required.
