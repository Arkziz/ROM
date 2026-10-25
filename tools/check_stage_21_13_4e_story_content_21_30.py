from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_start_path_21_30 import STORY_START_PATH_21_30,validate_story_start_path_21_30
validate_story_start_path_21_30();assert len(STORY_START_PATH_21_30)==10
print("Stage 21.13.4e Story content 21-30 smoke: PASS")
