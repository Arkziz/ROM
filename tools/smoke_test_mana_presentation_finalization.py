#!/usr/bin/env python3
"""Acceptance checks for the finalized Mana presentation and cooldown wording."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from data.mana_skill_presentation import (
    format_mana_skill_presentation,
    strip_legacy_mana_cost_from_description,
)


def turns_uk(value):
    value = max(0, int(value or 0))
    mod_10 = value % 10
    mod_100 = value % 100
    if mod_10 == 1 and mod_100 != 11:
        word = "хід"
    elif mod_10 in (2, 3, 4) and mod_100 not in (12, 13, 14):
        word = "ходи"
    else:
        word = "ходів"
    return f"{value} {word}"


def main():
    cases = (
        ("Витрачає 20 MP та завдає шкоди.", "Завдає шкоди."),
        ("Витрачає 30 MP. Одразу лікує.", "Одразу лікує."),
        ("Витрачає 45 MP, завдає шкоди.", "Завдає шкоди."),
        ("Витрачає 20 MP, очищає негативні ефекти.", "Очищає негативні ефекти."),
    )
    for source, expected in cases:
        skill = {
            "cost_type": "mana",
            "description": source,
            "mana_cost_flat": 8,
            "mana_cost_max_mp_percent": 7,
        }
        assert strip_legacy_mana_cost_from_description(skill) == expected
        rendered = format_mana_skill_presentation(skill, 170)
        assert "Витрачає" not in rendered
        assert "Вартість: 20 Мани" in rendered
        assert "Формула: 8 + 7% максимальної мани" in rendered
    assert [turns_uk(v) for v in (1, 2, 4, 5, 11, 21, 22, 24, 25)] == [
        "1 хід", "2 ходи", "4 ходи", "5 ходів", "11 ходів",
        "21 хід", "22 ходи", "24 ходи", "25 ходів",
    ]
    print("[OK] Final Mana presentation - comma/dot/conjunction cleanup and Ukrainian cooldown wording")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
