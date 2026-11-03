import ast
from pathlib import Path
T={"systems/auction_house_system.py":("update_expired_auction_lots",),"systems/guild_system.py":("make_existing_guild_icons_unique","_guild_cancel_other_pending_applications","accept_guild_application","create_guild_application"),"systems/player_interaction_system.py":("release_trade_inventory_reservations","_commit_player_trade_12_7_0"),"systems/player_system.py":("add_gold","add_kill"),"systems/pvp_system.py":("claim_pvp_round_resolution","release_pvp_round_resolution","complete_pvp_battle","recover_pvp_after_restart")}
for p,names in T.items():
 t=ast.parse(Path(p).read_text(encoding="utf-8-sig")); d=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
 for n in names:
  m=[x for x in d if x.name==n]; assert m,(p,n,"missing"); fn=m[-1]; calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]; assert any(x.func.attr=="commit" for x in calls),(p,n,"commit"); assert any(x.func.attr=="rollback" for x in calls),(p,n,"rollback")
print("PASS: Stage 21.4.14 active trade, PvP, guild and auction rollback invariants")
