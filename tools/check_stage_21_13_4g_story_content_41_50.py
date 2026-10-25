from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_start_path_41_50 import STORY_START_PATH_41_50,validate_story_start_path_41_50
validate_story_start_path_41_50();assert len(STORY_START_PATH_41_50)==10
print("Stage 21.13.4g Story content 41-50 smoke: PASS")
