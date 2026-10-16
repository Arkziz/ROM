# Stage 21.3.6 — ROM V2 CI baseline

- **Status:** `IMPLEMENTED`
- **Canonical runner:** `tools/run_v2_ci.py`
- **Hosted workflow:** `.github/workflows/rom-v2-ci.yml`

## Mandatory gates

1. Compile
2. Imports
3. Unit tests
4. Architecture enforcement
5. Duplicate scan
6. Content validation

The same canonical runner is executed locally and by hosted CI, so every commit is checked consistently.

Final baseline status: **PASS**.

## Next roadmap stage

Stage 21.4.1 — Domain value objects foundation.
