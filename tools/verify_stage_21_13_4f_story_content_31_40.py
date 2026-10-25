from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent;path=ROOT/"rom_v2/content/story_start_path_31_40.py";text=path.read_text(encoding="utf-8");ast.parse(text)
hits=[x for x in ("глава","start_path_041","dark_forest_051") if x.lower() in text.lower()]
if hits:print("Story content 31-40 boundary: FAIL",hits);sys.exit(1)
print("Stage 21.13.4f Story content 31-40 boundary: PASS")
