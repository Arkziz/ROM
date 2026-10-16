# ADR 21.2.2 — ROM V2 package structure

- **Status:** `PROPOSED_FOR_MANUAL_ACCEPTANCE`
- **Stage:** `21.2.2`
- **Parent ADR:** `ADR_21_2_1_V2_DEPENDENCY_RULES.md`

## Decision

Затвердити однозначний майбутній layout:

```text
rom_v2/
  domain/          # pure domain model and policy
  application/     # use cases, commands, queries and ports
  infrastructure/  # persistence and external adapters
  app/             # composition root and delivery adapters
  content/         # declarative validated catalogs
tests_v2/          # V2-only tests
tools/             # executable verification and maintenance tools
reports/           # machine evidence
MD/                # ADRs, contracts and runbooks
.runtime/v2/       # ignored runtime data, created in Stage 21.3.2
```

## Stage boundary

Stage 21.2.2 затверджує layout, ownership, naming і verifier. Фізичний `rom_v2` skeleton, bootstrap, dependency container, lifecycle та smoke test створюються тільки у Stage 21.3.1. Runtime directories створюються у Stage 21.3.2.

## Ownership

- `domain`: entities, value objects, policies, invariants, domain events.
- `application`: commands, queries, use cases, ports and transaction orchestration.
- `infrastructure`: repository/database/external adapter implementations.
- `app`: composition root, lifecycle and delivery adapters.
- `content`: declarative stable-key catalogs and validation-ready content.

## Prohibitions

- Catch-all modules such as `utils.py`, `helpers.py`, `common.py`, `service.py`, `manager.py`, `base.py`, `core.py` or `shared.py`.
- Business rules in `app`, SQL outside infrastructure, runtime mutation in content.
- Multiple package owners for the same responsibility.
- User-facing text as a technical identifier.

## Acceptance

Automated verifier must PASS. Manual acceptance must confirm that a new developer can unambiguously place representative files and that no catch-all package is required.

## Next roadmap stage

Stage 21.2.3 — Result and error model.
