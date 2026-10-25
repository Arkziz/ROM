from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_dark_forest_51_60 import STORY_DARK_FOREST_51_60,validate_story_dark_forest_51_60
validate_story_dark_forest_51_60();assert len(STORY_DARK_FOREST_51_60)==10
print("Stage 21.13.5c Story content 51-60 smoke: PASS")
