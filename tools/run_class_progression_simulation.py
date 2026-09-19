#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.class_progression import ClassProgressionRequest, run_class_progression


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="ROM Stage 18.30 class progression simulation")
    result.add_argument("--class", dest="character_class", required=True, choices=("warrior", "knight", "scout", "rogue", "mage", "priest"))
    result.add_argument("--target-level", type=int, required=True)
    result.add_argument("--seed", type=int, default=1)
    result.add_argument("--max-days", type=int, default=365)
    result.add_argument("--inventory-capacity", type=int, default=40)
    result.add_argument("--output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    request = ClassProgressionRequest(
        character_class=args.character_class,
        target_level=args.target_level,
        seed=args.seed,
        profile="hardcore",
        max_days=args.max_days,
        inventory_capacity=args.inventory_capacity,
    )
    payload = run_class_progression(ROOT, request)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + chr(10)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Report: {output}", file=sys.stderr)
    print(text, end="")
    return 0 if payload["target_reached"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
