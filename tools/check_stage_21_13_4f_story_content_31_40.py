from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_start_path_31_40 import STORY_START_PATH_31_40,validate_story_start_path_31_40
validate_story_start_path_31_40();assert len(STORY_START_PATH_31_40)==10
print("Stage 21.13.4f Story content 31-40 smoke: PASS")
