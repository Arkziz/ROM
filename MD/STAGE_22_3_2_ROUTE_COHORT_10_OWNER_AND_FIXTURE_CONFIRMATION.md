# Stage 22.3.2 route cohort 10 owner and fixture confirmation

- Status: **PASS_READ_ONLY**
- Patch revision: **1**
- Parent: `f4856a3006f895a08554f5f335f898a40b000a92`
- Exact pair: **288 → 336**
- Earlier route: **duel_placeholder**
- Later route: **pvp_duel_request**
- Canonical response owner: **handlers/pvp_interaction.py:pvp_duel_request**
- Prefix fixture: **PASS**
- Production mutation authorized: **false**
- Deletion authorized: **false**

## Decision

The earlier `duel_placeholder` route matches the same `pi:duel:` callback domain and is registered first, while the later `pvp_duel_request` route owns the user-visible response path. A guarded successor may retire only the exact earlier route after future-source validation, scoped backup, registration parity and rollback proof.

## Next formal step

`GO_TO_22_3_3_GUARDED_ROUTE_COHORT_10_MUTATION`
