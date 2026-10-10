# Stage 20.3.9 — Accept Hybrid Mana Economy

## Acceptance decision
Stage 20.3 is accepted after executable cross-layer verification and prior manual PvE/PvP verification.

## Accepted contract
- Six Mage/Priest Mana skills use hybrid cost `flat + Max MP percent`, `ROUND_HALF_UP`.
- PvE, PvP and simulator use canonical cost policy.
- Mana restores use canonical percentage policy and spend-before-restore.
- PvE and simulator post-combat floor is 50%, non-additive and non-reducing.
- Passive regeneration is 30% per full minute.
- Presentation shows effective cost and formula.
- Legacy runtime arithmetic is consolidated under `data/mana_policy.py`.

## Verification
Nine executable regressions, eight prerequisite reports, owner AST checks, exact commit history and database non-mutation evidence are required.

## Manual acceptance evidence
Earlier Stage 20.3 manual tests confirmed PvE Mage/Priest costs, insufficient Mana, Arcane Flow, Purify ordering, victory/escape/defeat floor paths and PvP Mage/Priest Mana behavior. No new manual scenario is required for this acceptance-only patch.

## Result
`Stage 20.3: ACCEPTED`. Next checklist stage is `20.4.1 Add 5 daily tokens`.
