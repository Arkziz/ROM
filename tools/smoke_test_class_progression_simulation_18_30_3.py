#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from systems.simulation.class_progression import ClassProgressionRequest, run_class_progression
first = run_class_progression(ROOT, ClassProgressionRequest("scout", 2, seed=1, max_days=30))
second = run_class_progression(ROOT, ClassProgressionRequest("scout", 2, seed=1, max_days=30))
assert first == second
assert first["target_reached"] is True
assert first["final_level"] == 2
assert first["battles"] >= first["wins"] >= 1
assert first["class"] == "scout"
print("[PASS] Stage 18.30.3 class progression deterministic level 1 to 2")
