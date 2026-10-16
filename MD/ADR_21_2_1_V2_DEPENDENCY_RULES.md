# ADR 21.2.1 — ROM V2 dependency rules

- **Status:** `ACCEPTED`
- **Stage:** `21.2.1`
- **Decision date:** `2026-10-16`
- **Verifier:** `tools/verify_v2_dependency_rules.py`

## Context

ROM V1 має цикли, broad facades, Telegram/SQLite coupling і неоднозначний dependency ownership. ROM V2 потребує одностороннього dependency graph, який перевіряється без імпорту runtime-коду.

## Decision

Внутрішні шари розташовані від найстабільнішого до зовнішнього:

```text
domain ← application ← infrastructure ← app
```

Дозволено:

- `domain` залежить лише від standard library і власних domain modules;
- `application` залежить від `domain` та application ports;
- `infrastructure` реалізує application ports і може залежати від `application` та `domain`;
- `app` є composition root і може wire усі внутрішні шари.

Заборонено:

- `domain → application|infrastructure|app`;
- `application → infrastructure|app`;
- `infrastructure → app`;
- Telegram framework, SQLite/ORM, HTTP clients, environment access і subprocess у `domain`;
- Telegram framework та SQLite/ORM у `application`;
- relative або absolute imports, що обходять заявлений напрям шарів.

## Ports and adapters

- Application визначає ports для repositories, Unit of Work, Clock, Random, notifications і external integrations.
- Infrastructure реалізує ports.
- Telegram handlers є adapters у зовнішньому `app`/adapter boundary, а не domain/application logic.
- SQLite schema, SQL і migrations належать infrastructure/database.

## Automated enforcement

- Current V2 modules: **0**.
- Current internal edges: **0**.
- Current violations: **0**.
- V2 tree currently empty: **True**.
- Verifier parses AST only and never imports project modules.
- Empty V2 tree is valid before scaffold creation; every future V2 Python file is automatically covered.

## Consequences

- New V2 code that violates dependency directions must fail automated acceptance.
- Concrete adapters cannot leak into domain or application.
- Composition and framework wiring remain replaceable.
- Exceptions require a new ADR; verifier suppression is not allowed by inline comments.

## Safety

Production code was not imported or executed. Production DB/WAL/SHM were not opened or modified.

## Next roadmap stage

Stage 21.2.2 — V2 package skeleton and application composition boundary.
