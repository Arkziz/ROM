#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HANDLER = ROOT / "handlers" / "runes.py"
SYSTEM = ROOT / "systems" / "rune_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    handler = HANDLER.read_text(encoding="utf-8-sig")
    system = SYSTEM.read_text(encoding="utf-8-sig")
    ast.parse(handler, filename=str(HANDLER))
    ast.parse(system, filename=str(SYSTEM))

    required_handler = (
        "RUNE_STAT_NAMES",
        "RUNE_LEVEL_ROMAN",
        'f"Руна {stat_name} {level_name}"',
        "RUNE_STAT_NAMES.get(preview['stat'], preview['stat'])",
    )
    for marker in required_handler:
        if marker not in handler:
            fail(f"handler localization marker missing: {marker}")

    if "RUNE_STAT_NAMES.get(preview['stat'], preview['stat'])" not in system:
        fail("success-message stat localization missing")

    forbidden = (
        "{rune['stat']} {rune['level']}",
        "до {preview['stat']}",
    )
    combined = handler + "\n" + system
    for marker in forbidden:
        if marker in combined:
            fail(f"technical stat label remains in user UI: {marker}")

    from data.runes import RUNE_STAT_NAMES
    expected = {
        "STR": "Сили",
        "STA": "Витривалості",
        "DEX": "Спритності",
        "INT": "Інтелекту",
        "WIS": "Мудрості",
    }
    if RUNE_STAT_NAMES != expected:
        fail(f"canonical Ukrainian stat names mismatch: {RUNE_STAT_NAMES}")

    print("[OK] Rune stat Ukrainian label contracts")
    print("- STR -> Сили")
    print("- STA -> Витривалості")
    print("- DEX -> Спритності")
    print("- INT -> Інтелекту")
    print("- WIS -> Мудрості")
    print("- occupied slot labels localized: OK")
    print("- confirmation bonus localized: OK")
    print("- insertion success bonus localized: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
