# Stage 21.16.2 - Direct-code migration and anti-overlay enforcement

## Decision

V2 production changes must edit the authoritative owner directly. Overlay modules,
monkey patches, runtime rebinding, shadow implementations, alias override chains and
import-order behavior are prohibited.

## Baseline semantics

Findings that already existed before this enforcement stage are recorded in
`reports/stage_21_16_2_direct_code_ownership_baseline.json`. They are not treated as
new regressions by this stage because Stage 21.16.2a owns their direct refactoring.
Any finding not present in that reviewed baseline is blocking.

## V1 boundary

V1 remains a read-only audit and parity reference. V2 runtime must not import,
execute or fall back to V1 production code.

## Failure reports

A patch failure is written only to a timestamped file beginning with
`stage_21_16_2_FAIL_`. The success report filename is never reused for recovery or
failure status.
