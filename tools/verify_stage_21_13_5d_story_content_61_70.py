from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent;path=ROOT/"rom_v2/content/story_dark_forest_61_70.py";text=path.read_text(encoding="utf-8");ast.parse(text)
hits=[x for x in ("глава","dark_forest_071","start_path_041") if x.lower() in text.lower()]
if hits:print("Story content 61-70 boundary: FAIL",hits);sys.exit(1)
print("Stage 21.13.5d Story content 61-70 boundary: PASS")
