# Stage 20.6.2 — Canonical Travel Presentation

Implemented the owner-approved spoiler-free texts for all four route directions.

- City map now explains the city, destination, travel time and preview action.
- Existing preview plus `🚶 Вирушити` remains the confirmation flow; no new screen was added.
- Preview, active travel and arrival use separate canonical route texts.
- Unknown nodes fail closed to `🧭 Невідома місцевість`; raw technical IDs are never displayed.
- Routes, unlock rules, duration (20 seconds), callbacks, persistence and database schema are unchanged.

Manual verification is required for the City map and all four route directions, including restart recovery arrival.
