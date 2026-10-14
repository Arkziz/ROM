# Stage 20.5.2 — Premium Combat Gold +25%

Premium now grants `+25%` combat gold for victories over normal, elite and boss enemies, matching the existing `+25% EXP` benefit. Gold is rounded to two decimal places using the canonical helper in `systems/timed_exp_bonus_system.py`.

The modifier is applied exactly once in `process_victory_reward`. The reward payload exposes base gold, Premium bonus gold and final gold. Victory UI shows the breakdown when the entitlement is active. Simulator parity is opt-in through `premium_active`; existing simulations remain non-Premium by default.

Quest rewards, item sales, auction, admin operations, refunds, guild rewards and contracts are unchanged. Premium loot remains absent and explicitly undecided. No database migration or retroactive gold is applied.

Manual verification: compare one normal/elite/boss victory without Premium and one with active Premium. Confirm final combat gold is base ×1.25 rounded to 0.01, UI shows the breakdown, and loot is unchanged.
