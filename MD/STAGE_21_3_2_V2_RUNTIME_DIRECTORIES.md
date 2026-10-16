# Stage 21.3.2 — ROM V2 runtime directories

- **Status:** `IMPLEMENTED`
- **Canonical owner:** `rom_v2.runtime_paths.RuntimePaths`
- **Runtime root:** `.runtime/v2`
- **Git policy:** runtime artifacts are ignored and never tracked

## Canonical directories

```text
.runtime/v2/
  db/
  logs/
  export/
  temporary/
```

## Ownership

`RuntimePaths` resolves, validates, and creates the four directories idempotently. Paths may not escape `.runtime/v2`. No V1 runtime path is imported.

## Git exclusion

The root `.gitignore` contains `.runtime/v2/`. Automated acceptance verifies each subtree with `git check-ignore` and verifies that `git ls-files` returns no runtime artifact.

## Evidence

- All directories ignored: **True**.
- No runtime files tracked: **True**.

## Next roadmap stage

Stage 21.3.3 — Configuration and secrets.
