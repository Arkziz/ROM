# Stage 19.26.4: Fix batch 31–40 quest-item handoff

QUEST_ITEM sources 34 and 37 now retain their item on source completion. TURN_IN quests 35 and 38 remain atomic exact-once consumers. The patch restores exactly one missing item only for users in the narrow defective state: source COMPLETED, paired turn-in ACTIVE, and total item quantity zero. No quest status is reset and no reward is reissued. After PASS, reopen the source NPC and complete the active TURN_IN normally.
