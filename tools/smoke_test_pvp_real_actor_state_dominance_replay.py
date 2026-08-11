from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems.pvp_real_actor_state_replay import build_real_actor,real_duel,run_replay
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}
mage=build_real_actor("mage"); assert mage.max_hp==415 and mage.max_mp==345 and mage.weapon_magical_min==9
knight=build_real_actor("knight"); assert knight.max_hp==435 and knight.physical_defense==78
scout=build_real_actor("scout"); assert scout.physical_attack==19 and scout.physical_crit_chance==7.69
one=real_duel("warrior","mage",10,14631); assert one["wins_a"]+one["wins_b"]+one["draws"]==10
report=run_replay(10,14631); assert len(report["real_actor_matrix"]["rows"])==15 and len(report["comparison"])==15
assert report["production_skill_catalog_used"] and report["target_aware_policy_used"] and report["production_database_writes"]==0
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() if (ROOT/n).exists() else None for n in ("game.db","game.db-wal")}; assert before==after
print("[OK] PvP real actor-state dominance replay fix")
print("- exact six real actor states: PASS")
print("- production skills and target-aware policy: PASS")
print("- real versus synthetic comparison: PASS")
print("- live balance changes: 0")
print("- production database writes: 0")
