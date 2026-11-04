# Stage 22.1.5 - Cross-File Key-Symbol Collision Reconciliation

- Status: **PASS_READ_ONLY**
- Parent: `1300573ccfc3069c8f4839f20f8b2922c3d5beb0`
- Collisions reconciled: **209**
- Blocking conflicts: **35**
- Canonical owner accepted: **NO**
- Deletion authorized: **NO**

## Classification counts

| Classification | Count |
|---|---:|
| `CROSS_LAYER_OWNER_CONFLICT` | 138 |
| `IDENTICAL_CROSS_FILE_DUPLICATE` | 1 |
| `RESOLVED_EXPLICIT_IMPORT_OWNER` | 24 |
| `SAME_LAYER_DOMAIN_COLLISION` | 10 |
| `TRANSACTION_OWNER_CONFLICT` | 35 |
| `UNREFERENCED_NAME_COLLISION` | 1 |

## Confidence counts

| Confidence | Count |
|---|---:|
| `BLOCKING` | 35 |
| `HIGH` | 172 |
| `LOW` | 1 |
| `MEDIUM` | 1 |

## Safety decision

This stage reconciles static cross-file evidence only. A ranked candidate is not an accepted canonical owner. Stage 22.1.6 must assign owner classifications before any no-delete or consolidation decision.

## Decision

**GO_TO_22_1_6_CANONICAL_OWNER_CLASSIFICATION**

- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**
