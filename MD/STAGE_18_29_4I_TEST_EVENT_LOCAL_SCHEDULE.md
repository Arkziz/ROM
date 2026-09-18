# ROM Stage 18.29.4i: Test Event Local Schedule

`START_LOCAL` and `END_LOCAL` in `events/test_event_2026/config.py` are now the only manually edited schedule values. Both use `DD.MM.YYYY HH:MM` in `Europe/Kyiv`. Runtime UTC boundaries are derived automatically and account for summer or winter offset.

Current window: `20.09.2026 00:17 <= Europe/Kyiv local time < 20.09.2026 00:32`.

For another test cycle, stop `main.py`, edit only `START_LOCAL` and `END_LOCAL`, run `python -m py_compile .\events\test_event_2026\config.py`, then restart `main.py`. The end must be later than the start. Reusing `test_event_2026` intentionally continues existing statistics, receipts, tokens and rewards.
