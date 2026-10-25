from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_dark_forest_91_100 import STORY_DARK_FOREST_91_100,validate_story_dark_forest_91_100
validate_story_dark_forest_91_100();assert len(STORY_DARK_FOREST_91_100)==10
print("Stage 21.13.5g Story content 91-100 smoke: PASS")
