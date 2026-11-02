# Stage 21.1.2 — Reliable polling single entrypoint

- Status: **PASS**
- Parent: `8eb4c7c744abf0b6b54dad8e408afe1ceaf6cc39`
- Production owner: `main.py`
- Recursive polling: removed
- External polling primitive owners: 1
- Backoff: exponential 2s to 30s, jitter bounded to 1s
- Fatal errors and shutdown signals: propagated
- Production SQLite: unchanged
- Manual game check: **REQUIRED**
