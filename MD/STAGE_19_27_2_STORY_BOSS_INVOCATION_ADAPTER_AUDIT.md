# Stage 19.27.2: Story boss invocation adapter audit

## Decision

`READY_FOR_STAGE_19_27_3_BATCH_41_50_CONTENT_AND_BOSS_POLICY`

## Recommended order

1. Complete this read-only technical audit.
2. Apply candidate content and boss policy in Stage 19.27.3.
3. Implement the narrow production adapter in a separate stage.
4. Run production-shaped boss lifecycle regressions.
5. Activate quests 41-50 only after those checks pass.

## Capability summary

- Look-around inline surface: `SUPPORTED`
- Canonical boss factory: `SUPPORTED`
- Victory-to-story-progress hook: `SUPPORTED`
- Permanent reply button: `NO`

## Canonical UX contract

- `👀 Роззирнутися` remains the temporary inline invocation surface.
- `⚔️ Полювання` remains unchanged and can still find the boss randomly.
- `🐺 Викликати Ватажка` appears only for quest 49 ACTIVE at 0/1 in `start_path`.
- `🧭 Як знайти Ватажка` is informational and never starts combat in the city.
- Defeat or escape preserves ACTIVE 0/1 and allows a later retry.
- Victory records 1/1 immediately and disables further forced invocation.

## Findings

- None.
