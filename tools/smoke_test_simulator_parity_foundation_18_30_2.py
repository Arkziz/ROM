#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.parity_foundation import (
    CanonicalOwnerResolver,
    SimulatorScenarioPolicy,
    build_isolated_state,
    validate_parity_foundation,
)

policy = SimulatorScenarioPolicy()
policy.validate()
state = build_isolated_state("scout", 1)
for _ in range(40):
    state.record_hunt(policy)
assert state.fatigue == 40
assert not state.can_hunt(policy)
assert state.recover_fatigue(policy, 4) == 0
assert state.fatigue == 40
assert state.recover_fatigue(policy, 5) == 1
assert state.fatigue == 39
assert state.can_hunt(policy)

left = build_isolated_state("mage", 991)
right = build_isolated_state("mage", 991)
assert [left.rng.random() for _ in range(20)] == [right.rng.random() for _ in range(20)]

owners = CanonicalOwnerResolver().validate_all()
assert "progression" in owners
assert "repair" in owners

result = validate_parity_foundation()
assert result["status"] == "PASS"
assert result["fatigue_after_recovery"] == 39
print("[PASS] Stage 18.30.2 simulator parity foundation contract")
print(json.dumps(result, ensure_ascii=False, sort_keys=True))
