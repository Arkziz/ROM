#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import events

readme = (ROOT / "events/README.md").read_text(encoding="utf-8-sig")
decision = (ROOT / "MD/STAGE_18_28_8_EVENT_BOSS_DEFER_DECISION.md").read_text(encoding="utf-8-sig")
boss_source = (ROOT / "systems/boss_system.py").read_text(encoding="utf-8-sig")
events_source = (ROOT / "events/__init__.py").read_text(encoding="utf-8-sig")

ast.parse(boss_source)
ast.parse(events_source)

assert "DEFER_EVENT_BOSS_INTEGRATION" in decision
assert "first approved production event" in decision
assert "event_boss_key" in decision
assert "collect_event_boss_candidates" in decision
assert "validated additive event-drop pipeline" in decision
assert "Stage 18.28.8 event boss defer decision" in readme
assert "first approved production event" in readme
assert "event_boss_key" in readme
assert "collect_event_boss_candidates" in readme

assert hasattr(events, "collect_event_boss_candidates")
assert events.EVENT_MODULES == ()
assert events.collect_event_boss_candidates({}, now=None) == ()
assert "def select_event_boss_candidate" not in events_source
assert "event_boss_key" not in boss_source
assert "event > boss > elite > normal" in boss_source

print("EVENT_BOSS_DEFER_CONTRACT_18_28_8A_OK")
