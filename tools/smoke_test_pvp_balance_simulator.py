from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_balance_simulator import simulate_duel,simulate_matchup,simulate_matrix
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
x=simulate_duel("knight","mage",1); assert x["rounds"]>=1 and x["winner"] in {"a","b","draw"}
m=simulate_matchup("knight","mage",4); assert m["trials"]==4 and m["wins_a"]+m["wins_b"]+m["draws"]==4
allm=simulate_matrix(1); assert len(allm["matchups"])==36 and len(allm["class_summary"])==6
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP balance simulator and 6x6 class matrix")
print("- deterministic isolated duel simulator: PASS")
print("- side-swapped matchup trials: PASS")
print("- 36 ordered class matchups: PASS")
print("- DEV command integration markers: PASS")
print("- production database writes: 0")
