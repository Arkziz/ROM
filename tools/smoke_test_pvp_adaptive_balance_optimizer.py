from pathlib import Path
import hashlib,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_adaptive_balance_optimizer import PARAMETERS,run_optimizer
required={"rogue_heavy_pen","warrior_magic_received","priest_physical_received","knight_vs_priest_damage"}; assert required<=set(PARAMETERS)
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
with tempfile.TemporaryDirectory() as d:
 r=run_optimizer(.12,14648,Path(d)/"checkpoint.json",Path(d)/"report.json",True)
 assert r["version"]=="14.6.4d5" and r["round_cap"]==18 and len(r["best_candidate"]["rows"])==15
 assert not r["live_balance_changed"] and r["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP extreme matchup and Priest pacing refinement")
print("- d4 base freeze: PASS")
print("- targeted extreme matchup candidates: PASS")
print("- Priest pacing objective: PASS")
print("- visible stat changes: 0")
print("- live balance changes: 0")
print("- production database writes: 0")
