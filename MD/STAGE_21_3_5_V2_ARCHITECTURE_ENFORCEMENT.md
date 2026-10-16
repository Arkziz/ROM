# Stage 21.3.5 — ROM V2 architecture enforcement

- **Status:** `IMPLEMENTED`
- **Verifier:** `tools/verify_v2_architecture.py`
- **Criterion:** verifier returns `PASS`

## Enforced rules

- Required V2 foundation files exist.
- V1 runtime imports are forbidden.
- Domain/application cannot import Telegram or database drivers.
- Inward dependency direction is enforced.
- Catch-all modules are forbidden.
- Canonical UoW, Clock, and RandomSource owner counts are enforced.

## Evidence

- Physical files: **19**.
- Import edges: **39**.
- Violations: **0**.

## Next roadmap stage

Stage 21.3.6 — CI foundation.
