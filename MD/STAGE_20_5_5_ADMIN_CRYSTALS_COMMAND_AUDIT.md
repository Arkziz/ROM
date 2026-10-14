# Stage 20.5.5 — Admin Crystals Audit

**ROOT_CAUSE_FOUND**

`/admin_crystals`, menu and wizard work. `admin_crystal_credit_audit` is absent. Its idempotent initializer exists, but `main.py` neither imports nor calls it, and no equivalent migration exists. Stage 20.5.6 must wire the initializer before handler registration and test credit, debit, clamped debit, replay, history and detail. Production code and DB were unchanged.
