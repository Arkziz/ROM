# Stage 21.4.6 — Crystal and currency transaction atomicity

- Status: **PASS**
- Parent: `1b5cfe1e8c6c6f4d5e855182e6a989e4110ff245`
- Hardened owners: `preview_admin_adjustment`, `compensate_crystal_transaction`
- Existing business transactions and caller-owned `_stack`: **PRESERVED**
- Rollback and re-raise: **YES**
- Injected-failure smoke: **PASS**
- DB/WAL/SHM patch mutations: **NONE**
- Manual game check: **REQUIRED**
