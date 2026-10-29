# Stage 21.16.3a - V1 reference-isolation contract

## Decision

ROM V1 is reference evidence only. ROM V2 production runtime must not import,
execute, register, call, or fall back to V1 or `legacy/v1`.

## Permitted access

Only explicit read-only audit and parity-fixture construction may read V1 files.
Such tooling must operate on file content or serialized evidence and must not
place V1 packages on the production import path.

## Forbidden access

- static or dynamic imports from V1 root namespaces or `legacy/v1`;
- calling V1 handlers, services, repositories, formulas, routers, entrypoints;
- fallback to V1 when a V2 capability is missing;
- shared mutable runtime state or shared Telegram registration;
- mutation of V1 reference files by migration or runtime code;
- overlays, monkey patches, shadow implementations, runtime rebinding.

## Enforcement

`python -m tools.check_v2_v1_reference_isolation` performs a non-recursive AST
scan of `rom_v2`. Full physical isolation is completed during Stage 21.22 when
V1 is moved to `legacy/v1`; this stage defines and verifies the contract only.

## Runtime status

Telegram runtime: NOT_CONNECTED. Production persistence: NOT_CONNECTED.
Manual game check: NOT_REQUIRED.
