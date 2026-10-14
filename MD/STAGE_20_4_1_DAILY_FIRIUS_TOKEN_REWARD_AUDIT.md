# Stage 20.4.1 — Daily Firius Token Reward Audit

## Decision
`PASS / GO` for mutation Stage 20.4.1a. Production code is unchanged.

## Exact owner map
- Canonical quantity: `data/runes.py::FIRIUS_TOKENS_PER_DAILY_REWARD = 5`.
- Actual atomic grant and claim response: `systems/rune_system.py`, both consume the canonical constant.
- Preview: `handlers/daily.py`, currently hardcoded `Жетон Фіріуса ×5`.
- Public route: `db_modules/systems_wrappers.py` delegates to the rune-system claim owner.
- Potion reward: `data/balance.py`, item 401 ×3.

## Findings
1. `FIRIUS-DAILY-001 HIGH OPEN`: canonical quantity must change from 5 to approved 3.
2. `FIRIUS-DAILY-002 HIGH OPEN`: preview must use the canonical constant instead of hardcoded ×5.
3. Exact-once claim, atomic bag capacity and rollback are already present.
4. No retroactive token debit path exists.

## Mutation scope
Stage 20.4.1a may modify only `data/runes.py` and `handlers/daily.py`, plus tests/docs. It must not modify potion quantity, token item ID, fusion reward, existing balances, DB schema, WAL or SHM.

## Manual verification
Required after mutation: preview, one successful claim, second-claim rejection, exact +3 token delta and unchanged pre-existing balance except the +3 grant.
