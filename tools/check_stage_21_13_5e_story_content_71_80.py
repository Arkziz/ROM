from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from rom_v2.content.story_dark_forest_71_80 import STORY_DARK_FOREST_71_80,validate_story_dark_forest_71_80
validate_story_dark_forest_71_80();assert len(STORY_DARK_FOREST_71_80)==10
print("Stage 21.13.5e Story content 71-80 smoke: PASS")
