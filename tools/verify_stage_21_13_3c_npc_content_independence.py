from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/npc_dialogue_model.py",ROOT/"rom_v2/application/npc_dialogue_service.py"]
for path in files:
 text=path.read_text(encoding="utf-8");ast.parse(text)
 forbidden=("STORY_QUEST_NPCS","start_path","dark_forest","Староста","Алхімік","Коваль","shop_service","auction_service","guild_service")
 hits=[x for x in forbidden if x in text]
 if hits:print(f"NPC content independence: FAIL {path.name}:{hits}");sys.exit(1)
print("Stage 21.13.3c NPC content independence: PASS")
