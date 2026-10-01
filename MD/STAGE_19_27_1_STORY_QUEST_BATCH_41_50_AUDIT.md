# Stage 19.27.1: Story quest batch 41-50 audit

## Decision

`READY_FOR_STAGE_19_27_2_BATCH_41_50_CONTENT_AND_BOSS_REVIEW`

## Scope

Read-only audit of candidate quests 41-50, production boundary 1-40, NPC routes, item reveal lifecycle, rewards as authored, and the planned boss encounter contract.

## Boss contract

Decision: `NEEDS_CANONICAL_HUNT_ADAPTER_REVIEW`

The audit does not implement or activate a boss. Activation is blocked until a production-shaped test proves use of the canonical Hunt/combat pipeline, player-level boss generation, and absence of a permanent separate boss button.

## Findings

- `REVIEW` `ITEM_REVEAL_BEFORE_DROP`: {"severity": "REVIEW", "code": "ITEM_REVEAL_BEFORE_DROP", "quest": 46, "display_name": "Клоччя шерсті Ватажка", "fields": ["q46.objective_text"]}

## Structural errors

- None.
