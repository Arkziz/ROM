# Stage 21.8.7 - Monolith Reduction Acceptance and Closure

- Status: **CLOSED_ACCEPTED**
- Stage 21.8: **CLOSED_ACCEPTED**
- Parent: `b9cc8264fec08d75f06fa70123f074b69ebb8a87`
- Accepted slice: **`build_lethal_combat_log`**
- Canonical owner: **`handlers/combat_formatting.py`**
- Combat line delta: **-64**
- Combat top-level function delta: **-1**
- Byte-parity fixtures: **5**
- Runtime acceptance: **PASS**
- Single reward exports: **2/2**
- Telegram registration changed: **NO**
- Unresolved blockers: **0**
- Dev wrapper chain: **DEFERRED_OUT_OF_CLOSURE**
- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**
- Next formal step: **GO_TO_STAGE_21_9_1**

## Evidence levels

- API_READY: **YES**
- ADAPTER_CONNECTED: **YES**
- RUNTIME_DISPATCH_VERIFIED: **YES**
- END_TO_END_ACCEPTED: **YES**

The independent four-definition `register_dev_handlers` wrapper chain remains deferred. The deferred scope is not a blocker for the accepted minimal behavior-preserving Stage 21.8 extraction.
