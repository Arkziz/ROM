import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for rel in ("keyboards.py","handlers/profile.py","systems/profile_history_system.py"):ast.parse((R/rel).read_text(encoding="utf-8"),filename=rel)
k=(R/"keyboards.py").read_text(encoding="utf-8");p=(R/"handlers/profile.py").read_text(encoding="utf-8");m=(R/"systems/profile_history_system.py").read_text(encoding="utf-8")
assert 'kb.row("🎒 Інвентар", "📜 Історія")' in k
assert 'active_tab != "history"' not in p and 'profile_history_reply_message_17_24_1_1' in p
assert 'PVP_REASON_UA' in m and 'localize_pvp_reason' in m and "'afk_defeat':'поразка через бездіяльність'" in m
sys.path.insert(0,str(R));from systems.profile_history_system import localize_pvp_reason
assert localize_pvp_reason('afk_defeat',False)=='поразка через бездіяльність'
assert localize_pvp_reason('afk_defeat',True)=='перемога через бездіяльність суперника'
assert localize_pvp_reason('unknown_reason',False)=='бій завершено'
print("[PASS] Stage 17.24.1.1 profile button and PvP localization")
