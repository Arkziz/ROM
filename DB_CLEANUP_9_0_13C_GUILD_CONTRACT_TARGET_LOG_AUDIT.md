# ROM 9.0.13c — Guild Contract Target Log Audit

Generated: `2026-07-29T23:29:59`

## Safety

- Gameplay files changed: **0**
- Database rows changed: **0**
- Database SHA/size/mtime unchanged: **True**
- Database quick check: **ok**

## Contract pipeline

- `get_active_contract()` exposes `target_mob_name`: **yes**
- Claim snapshots contract before base claim: **yes**
- Base claim deletes active contract: **yes**
- Saved snapshot passed as `contract=contract`: **yes**
- Guild hook call keyword sets: `[['contract', 'user_id']]`

## Guild formatter

- Accepted keys: `['name', 'title', 'contract_name']`
- Accepts `target_mob_name`: **False**
- Isolated generated reason: `Виконання контракту: контракт.`
- Target preserved: **False**
- Generic fallback reproduced: **True**

## Existing data

- Exact historical fallback log rows detected: **0**

## Diagnosis

Guild formatter ignores target_mob_name and falls back to 'контракт'. The Contract System already snapshots the full contract before deletion and passes it to the Guild hook.

## Recommended hotfix

1. Add `target_mob_name` as the first canonical lookup key in `award_guild_contract_completion()`.
2. Preserve `name`, `title`, and `contract_name` as backward-compatible fallbacks.
3. Add isolated contracts proving the target name reaches the Guild log reason.
4. Do not rewrite historical generic rows because their original target cannot be reliably reconstructed.

Suggested next patch: `patch_9_0_13d_guild_contract_target_log_hotfix.py`
