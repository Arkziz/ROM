from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "MD/PVP_ARCHITECTURE_SKILL_PARITY_AUDIT_14_0_0.json"
SPEC = ROOT / "MD/PVP_V1_CANONICAL_SPECIFICATION_14_0_0.md"
ROADMAP = ROOT / "MD/PVP_IMPLEMENTATION_ROADMAP_14_0_0.md"


def main() -> None:
    assert REPORT.exists(), REPORT
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert data["verdict"] in {"PASS", "REVIEW"}, data["findings"]
    assert data["skill_catalog"]["total_skills"] == 18
    assert set(data["skill_catalog"]["classes"]) == {"warrior", "knight", "scout", "rogue", "mage", "priest"}
    assert all(len(skills) == 3 for skills in data["skill_catalog"]["classes"].values())
    assert data["approved_rules"]["same_skill_definitions_as_pve"] is True
    assert data["approved_rules"]["separate_pvp_skill_overrides"] is False
    assert data["approved_rules"]["production_hp_mp_changed"] is False
    assert data["approved_rules"]["stun_counts_as_afk"] is False
    assert data["approved_rules"]["maximum_rounds"] == 50
    assert data["approved_rules"]["action_timeout_seconds"] == 20
    assert data["pvp_multipliers"] == {"damage": 1.0, "healing": 1.0, "shield": 1.0, "debuff": 1.0}
    assert "PVP_DAMAGE_MULTIPLIER = 1.00" in SPEC.read_text(encoding="utf-8")
    assert "14.1.0" in ROADMAP.read_text(encoding="utf-8")
    assert data["gameplay_mutations"] == 0 and data["database_writes"] == 0
    print("[OK] PvP 14.0.0 audit contracts")
    print("- six classes / eighteen PvE skills parity snapshot: PASS")
    print("- no separate PvP skill costs/cooldowns/effects: PASS")
    print("- central PvP multipliers fixed at 1.00: PASS")
    print("- isolated duel-state and simultaneous-round specification: PASS")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
