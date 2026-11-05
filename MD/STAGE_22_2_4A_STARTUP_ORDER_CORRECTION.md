# Stage 22.2.4a startup order correction

- Status: **PASS_READ_ONLY**
- Patch revision: **1**
- Parent: `4a35a289ed683127699d9c2543dc17e3bbf279eb`
- Primary entrypoint: `main.py`
- Polling entrypoints: **2**
- Relevant startup calls: **48**
- Expected present categories ordered: **False**
- Blocking startup anomalies: **2**
- Production mutation authorized: **false**
- Deletion authorized: **false**

## Method
Current V1 Python sources were parsed with AST. The patch records migration, recovery, registration, worker, polling and shutdown calls in source order without importing or executing `main.py`, workers or polling.

## Decision
`GO_TO_22_2_5A_DB_TRANSACTION_OWNER_AND_EXACT_ONCE_CORRECTION`
