from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from rom_v2.content.story_start_path_1_10 import STORY_START_PATH_1_10,validate_story_start_path_1_10
validate_story_start_path_1_10();assert len(STORY_START_PATH_1_10)==10
print("Stage 21.13.4c Story content 1-10 smoke: PASS")
