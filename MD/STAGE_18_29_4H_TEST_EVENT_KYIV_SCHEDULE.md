# ROM Stage 18.29.4h: Test Event Kyiv Schedule

The pilot event is enabled for the half-open Europe/Kyiv interval `19.09.2026 00:15 <= local time < 19.09.2026 00:30`. The canonical UTC boundaries are `2026-09-18 21:15Z` and `2026-09-18 21:30Z`.

To run the same test event again, stop `main.py`, edit only `events/test_event_2026/config.py`, update `START_LOCAL` and `END_LOCAL`, then update `START_AT` and `END_AT` to the exact UTC equivalents. Keep `ENABLED = True`, ensure start is earlier than end, compile the file, and restart `main.py`. Reusing the same `EVENT_KEY` intentionally continues existing statistics, receipts, tokens and rewards.
