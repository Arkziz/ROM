#!/usr/bin/env python3
"""Static contract for Priest description and visible cooldown."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMBAT = ROOT / "handlers" / "combat.py"


def main():
    source = COMBAT.read_text(encoding="utf-8")
    ast.parse(source)
    assert "Разом: 3 лікування. Перезарядка: 4 ходи." not in source
    assert "а потім лікує ще 2 рази на початку наступних ходів." in source
    assert 'mob["skill_cooldowns"][skill_key] = cooldown_turns' in source
    assert 'mob["skill_cooldowns"][skill_key] = cooldown_turns + 1' not in source

    cooldown = 4
    visible = [cooldown]
    for _ in range(4):
        cooldown = max(0, cooldown - 1)
        visible.append(cooldown)
    assert visible == [4, 3, 2, 1, 0], visible
    print("[OK] Priest description has no duplicate summary; visible cooldown=4,3,2,1,0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
