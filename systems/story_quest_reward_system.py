"""Same-connection production reward adapter for story quest completion."""
from __future__ import annotations
from systems.player_system import apply_exp_in_transaction, apply_gold_in_transaction


def build_story_quest_reward_adapter(*, exp: int, gold):
    """Return an adapter compatible with complete_active_story_quest.

    All mutations use the supplied canonical connection. The adapter never
    starts, commits or rolls back a transaction and never sends Telegram output.
    """
    exp_amount = int(exp)
    gold_amount = float(gold)
    if exp_amount < 0 or gold_amount < 0:
        raise ValueError("story quest rewards cannot be negative")

    def reward_adapter(*, connection, user_id, quest, idempotency_key):
        exp_result = apply_exp_in_transaction(connection, user_id, exp_amount)
        if exp_result is None:
            raise ValueError(f"unknown user_id: {user_id}")
        gold_balance = apply_gold_in_transaction(connection, user_id, gold_amount)
        return {
            "quest_id": quest.quest_id,
            "idempotency_key": str(idempotency_key),
            "exp_awarded": exp_amount,
            "gold_awarded": gold_amount,
            "gold_balance": gold_balance,
            "exp_result": exp_result,
        }
    return reward_adapter
