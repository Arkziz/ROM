# Stage 19.23.3l: PVE cursor and stale callback containment

PvE auto-escape no longer reuses the process-global SQLite cursor. Expired Telegram callback acknowledgements are contained only for answer_callback_query, while unrelated HTTP 400 and existing 429 behavior remain unchanged. Manual hunting and restart verification is required.
