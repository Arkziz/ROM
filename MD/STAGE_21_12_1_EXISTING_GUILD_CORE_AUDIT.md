# Stage 21.12.1 - Existing V1 Guild Core audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- Implementation authorized: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Confirmed V1 constants

- Creation cost: **50.00 gold**
- Minimum level: **3**
- Default member limit: **10**

## Contract matrix

- `GUILD_CORE_OWNER_AND_SCHEMA`: **V1_CONFIRMED** - Exact V1 evidence confirmed.
- `CREATION_COST_LEVEL_AND_LIMIT`: **V1_CONFIRMED** - Exact V1 evidence confirmed.
- `NAME_TAG_ICON_IDENTITY_POLICY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.
- `MEMBERSHIP_AND_ROLE_INVARIANTS`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.
- `CREATION_ATOMICITY_AND_GOLD_DEBIT`: **V1_CONFIRMED** - Exact V1 evidence confirmed.
- `DUPLICATE_GUILD_AND_MEMBERSHIP_POLICY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.
- `PERMISSIONS_AND_MANAGEMENT_BOUNDARY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.
- `LEAVE_TRANSFER_AND_DISSOLUTION_BOUNDARY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.
- `PERSISTENCE_RESTART_AND_FAILURE_POLICY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.
- `HANDLER_REGISTRATION_AND_CONSUMER_BOUNDARY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact invariant, permission, lifecycle or failure contract requires refinement.

## Next patch

`patch_21_12_1a_refine_guild_core_contract.py`
