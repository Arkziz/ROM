# Stage 22.2.4 route overlap, shadow, duplicate-response and dead-path classification

- Status: **PASS_READ_ONLY**
- Patch revision: **1**
- Parent: `1599a54afa9e391e1d2670b55231854ad4541327`
- Registrations: **375**
- Exact static duplicate pairs: **37**
- Overlap candidates: **5**
- Shadow candidates/proven-static pairs: **42**
- Duplicate-response risk pairs: **42**
- Dead-path candidates: **364**
- Deletion authorized: **false**
- Production mutations: **NONE**
- Production SQLite opened: **false**

## Classification policy
`PROVEN_STATIC` means equality is established from source registration/filter evidence. `CANDIDATE` requires later production-shaped dispatch verification. Absence of a static direct call does not prove a Telegram route dead because dispatcher invocation is indirect.

## Decision
`GO_TO_22_2_5_PRODUCTION_SHAPED_DISPATCH_AND_DUPLICATE_RESPONSE_VERIFICATION`
