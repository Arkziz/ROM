# Stage 20.6.1 — Travel Presentation Audit

**CANONICAL_TEXT_METADATA_DESIGN_READY**

## Routes

- `city → start_path`: 🏙️ Місто → 🌿 Початок Шляху
- `start_path → city`: 🌿 Початок Шляху → 🏙️ Місто
- `start_path → dark_forest`: 🌿 Початок Шляху → 🌲 Темний Бір
- `dark_forest → start_path`: 🌲 Темний Бір → 🌿 Початок Шляху

## Presentation states

- `route_selection`: present
- `route_preview`: present
- `confirmation`: gap
- `travel_started`: present
- `active_travel`: present
- `arrival`: present
- `restart_recovery`: present
- `cancel_or_unavailable`: present

## Findings

- **TRAVEL_TEXT_001 · MEDIUM** — No canonical per-route/per-state presentation metadata; texts live in handler/system literals.
- **TRAVEL_TEXT_002 · MEDIUM** — _node_name falls back to raw node_id, allowing technical IDs in exceptional UI paths.
- **TRAVEL_TEXT_003 · MEDIUM** — Not all eight travel presentation states have an explicit independently detectable text contract.

## Stage 20.6.2 design

- Canonical route/state metadata, separate preview/start/active/arrival texts.
- Never expose raw `location_id`; resolver must fail closed to localized generic text.
- Atmospheric but spoiler-free text only.
- Routes, duration and persistence semantics remain unchanged.

Production code and DB were not changed. Manual verification is not required.
