from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/story_navigation.py",ROOT/"rom_v2/application/story_navigation_service.py",ROOT/"rom_v2/presentation/story_navigation.py"]
for p in files:ast.parse(p.read_text(encoding="utf-8"))
text="\n".join(p.read_text(encoding="utf-8") for p in files)
for bad in ("from handlers.","from db_modules.","import sqlite3","import aiogram"):
 if bad in text:print("Story navigation boundary: FAIL",bad);sys.exit(1)
print("Stage 21.13.6c Story navigation boundary: PASS")
