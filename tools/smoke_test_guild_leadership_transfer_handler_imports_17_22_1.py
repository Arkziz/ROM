import ast, importlib, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
source=(R/"handlers/guild.py").read_text(encoding="utf-8")
ast.parse(source,filename="handlers/guild.py")
module=importlib.import_module("handlers.guild")
required=("get_user_guild_role","get_user_guild","get_guild_member","get_character_name_by_user_id","transfer_guild_leadership","transfer_guild_leadership_and_leave")
missing=[name for name in required if not callable(getattr(module,name,None))]
assert not missing, missing
assert "👑 Передати керівництво" in source
print("[PASS] Stage 17.22.1 guild handler runtime imports")
