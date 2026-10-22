"""Pure Premium combat reward modifier.

This module applies the source-faithful Premium modifier only to finalized
combat EXP and combat gold. It owns no clock, persistence, loot, presentation,
runtime wiring, or non-combat reward policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

ACTIVE_MULTIPLIER = Decimal("1.25")
INACTIVE_MULTIPLIER = Decimal("1.0")
CENT = Decimal("0.01")

@dataclass(frozen=True, slots=True)
class PremiumCombatSnapshot:
    active: bool

@dataclass(frozen=True, slots=True)
class PremiumCombatBreakdown:
    premium_active: bool
    exp_base: int
    exp_bonus: int
    exp_final: int
    gold_base: Decimal
    gold_bonus: Decimal
    gold_final: Decimal
    multiplier: Decimal

class PremiumCombatModifier:
    """Apply Premium exactly once to combat-only rewards."""

    def apply(self, *, base_combat_exp: int, base_combat_gold: Decimal,
              premium_active_snapshot: PremiumCombatSnapshot) -> PremiumCombatBreakdown:
        exp_base = max(0, int(base_combat_exp))
        gold_base = self._money(max(Decimal("0"), Decimal(base_combat_gold)))
        multiplier = ACTIVE_MULTIPLIER if premium_active_snapshot.active else INACTIVE_MULTIPLIER
        exp_bonus = (exp_base * 25) // 100 if premium_active_snapshot.active else 0
        exp_final = exp_base + exp_bonus
        gold_final = self._money(gold_base * multiplier)
        gold_bonus = self._money(gold_final - gold_base)
        return PremiumCombatBreakdown(
            premium_active=premium_active_snapshot.active,
            exp_base=exp_base, exp_bonus=exp_bonus, exp_final=exp_final,
            gold_base=gold_base, gold_bonus=gold_bonus, gold_final=gold_final,
            multiplier=multiplier,
        )

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(CENT, rounding=ROUND_HALF_EVEN)
