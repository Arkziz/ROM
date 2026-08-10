from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_production_fixture_audit import format_summary,run_audit
before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}
fixture={"version":"14.6.2d","verdict":"PASS","trials":10,"actors":{str(i):{} for i in range(6)},"skills":{"skills_checked":18},"matrix_integrity":{"pass":True,"max_side_delta_pp":40.0,"side_delta_review":True},"modifier_sensitivity":{"all_observable":True},"fixture_slot_parity":{"pass":True},"fixture_warnings":{"review":True}}
text=format_summary(fixture)
assert "Slot-weighted fixture parity: PASS" in text
assert "Fixture balance spread: REVIEW" in text
assert "Statistical confidence: REVIEW (10 trials/direction)" in text
assert "Side-order sensitivity: REVIEW" in text
assert "Fixture parity: REVIEW" not in text
result=run_audit(2,10,"rare")
assert result["verdict"]=="PASS" and result["fixture_slot_parity"]["pass"] is True
runtime_text=format_summary(result)
assert "Slot-weighted fixture parity: PASS" in runtime_text
assert "Fixture balance spread:" in runtime_text
assert "Statistical confidence: REVIEW (2 trials/direction)" in runtime_text
after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() if (ROOT/name).exists() else None for name in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP fixture summary and statistical review fix")
print("- slot parity and balance spread are separated: PASS")
print("- low-sample statistical review is explicit: PASS")
print("- side-order review is explicit: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
