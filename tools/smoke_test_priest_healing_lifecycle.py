#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from data.priest_healing_policy import *

def main():
    assert PRIEST_HEALING_DURATION_TURNS == 2
    assert PRIEST_HEALING_COOLDOWN_TURNS == 4
    assert PRIEST_HEALING_REAPPLICATION_POLICY == "replace"
    effect = build_priest_healing_effect(13)
    ticks = []
    while effect["turns"] > 0:
        ticks.append(effect["heal"])
        effect["turns"] -= 1
    assert ticks == [13, 13]
    effects = {PRIEST_HEALING_EFFECT_KEY: build_priest_healing_effect(10)}
    effects[PRIEST_HEALING_EFFECT_KEY] = build_priest_healing_effect(20)
    assert effects[PRIEST_HEALING_EFFECT_KEY]["heal"] == 20
    assert effects[PRIEST_HEALING_EFFECT_KEY]["turns"] == 2
    cooldown = PRIEST_HEALING_COOLDOWN_TURNS
    blocked = []
    for _ in range(4):
        blocked.append(cooldown > 0)
        cooldown = max(0, cooldown - 1)
    assert blocked == [True, True, True, True] and cooldown == 0
    print("[OK] Priest healing lifecycle: duration=2 cooldown=4 replace")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
