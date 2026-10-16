# ADR 21.2.7 — ROM V2 code and comment standards

- **Status:** `ACCEPTED`
- **Criterion:** `Lintable coding standard`

## Type hints

Every public function and method has typed parameters and an explicit return type. Public attributes are typed. `Any` requires a documented boundary reason.

## Docstrings

Public modules, classes, functions and methods require docstrings that describe contract, invariants and failure behavior rather than repeating implementation syntax.

## Comments

Comments explain reasons and non-obvious invariants. Comments are required around rounding, ordering, atomicity, idempotency, restart semantics and workarounds. Comments that restate obvious code are forbidden. TODO/FIXME requires a Stage or issue reference.

## Naming and ownership

English snake_case is used for modules/functions and PascalCase for types. Catch-all modules and duplicate production owners are forbidden.

## Exceptions

Bare except and silent exception swallowing are forbidden. Expected business outcomes use typed Result. Translated exceptions preserve chaining.

## Automated evidence

- Physical V2 exists: **False**.
- Files checked: **0**.
- Public APIs checked: **0**.
- Violations: **0**.

## Next roadmap stage

Stage 21.3.1 — Minimal V2 package skeleton and isolated bootstrap.
