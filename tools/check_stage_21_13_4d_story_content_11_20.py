from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_start_path_11_20 import STORY_START_PATH_11_20,validate_story_start_path_11_20
validate_story_start_path_11_20();assert len(STORY_START_PATH_11_20)==10
print("Stage 21.13.4d Story content 11-20 smoke: PASS")
