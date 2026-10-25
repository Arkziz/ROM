from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_dark_forest_81_90 import STORY_DARK_FOREST_81_90,validate_story_dark_forest_81_90
validate_story_dark_forest_81_90();assert len(STORY_DARK_FOREST_81_90)==10
print("Stage 21.13.5f Story content 81-90 smoke: PASS")
