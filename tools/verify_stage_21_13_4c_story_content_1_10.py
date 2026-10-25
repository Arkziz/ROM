from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent
path=ROOT/"rom_v2/content/story_start_path_1_10.py";text=path.read_text(encoding="utf-8");ast.parse(text)
forbidden=("dark_forest","Темний Бір","глава")
hits=[x for x in forbidden if x.lower() in text.lower()]
if hits:print(f"Story content 1-10 boundary: FAIL {hits}");sys.exit(1)
print("Stage 21.13.4c Story content 1-10 boundary: PASS")
