# Stage 21.12.2 - Existing V1 Guild Applications/Management audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- Implementation authorized: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Application statuses

- `GUILD_APPLICATION_PENDING`: `pending`
- `GUILD_APPLICATION_ACCEPTED`: `accepted`
- `GUILD_APPLICATION_REJECTED`: `rejected`
- `GUILD_APPLICATION_CANCELLED`: `cancelled`

## Contract matrix

- `APPLICATION_OWNER_AND_STATUS_MODEL`: **V1_CONFIRMED** - Exact V1 evidence confirmed.
- `APPLICATION_CREATE_CANCEL_POLICY`: **V1_CONFIRMED** - Exact V1 evidence confirmed.
- `APPLICATION_ACCEPT_ATOMICITY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `APPLICATION_REJECT_POLICY`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `MEMBER_LIMIT_AND_ELIGIBILITY_RECHECK`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `ROLE_PROMOTION_AND_OFFICER_LIMIT`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `MEMBER_KICK_AND_SELF_PROTECTION`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `MANAGEMENT_PERMISSION_MATRIX`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `DUPLICATE_HANDLER_REGISTRATION_RISK`: **REVIEW_REQUIRED** - V1 behavior discovered; exact atomicity, permission, idempotency or handler contract requires refinement.
- `PERSISTENCE_RESTART_AND_FAILURE_POLICY`: **V1_CONFIRMED** - Exact V1 evidence confirmed.

## Next patch

`patch_21_12_2a_refine_guild_applications_management_contract.py`
