from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_dark_forest_61_70 import STORY_DARK_FOREST_61_70,validate_story_dark_forest_61_70
validate_story_dark_forest_61_70();assert len(STORY_DARK_FOREST_61_70)==10
print("Stage 21.13.5d Story content 61-70 smoke: PASS")
