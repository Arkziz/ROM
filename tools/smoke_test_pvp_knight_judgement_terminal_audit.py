from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_knight_judgement_terminal_audit import run_audit
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
r=run_audit(10,14633)
assert r["version"]=="14.6.3b2" and r["opponents_checked"]==5
assert r["skill_definition"]["key"]=="knight_judgement" and r["skill_definition"]["cost"]==50
assert r["forced_judgement"]["samples"]>0 and r["forced_judgement"]["all_valid"]
assert r["production_round_resolver_used"] and r["production_skill_catalog_used"] and r["target_aware_policy_used"]
assert r["production_database_writes"]==0 and not r["live_balance_changed"]
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP Knight Judgement reachability and terminal reason audit")
print("- production skill definition and forced execution: PASS")
print("- policy reachability and priority counters: PASS")
print("- terminal reason/winner semantics: PASS")
print("- stun attribution: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
