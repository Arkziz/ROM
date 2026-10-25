from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from types import SimpleNamespace
from rom_v2.application.story_navigation_service import StoryNavigationService
q=[SimpleNamespace(number=n,quest_id=f"q{n}",title=f"Квест {n}",quest_type="KILL",target_quantity=1,objective_text=f"Ціль {n}") for n in range(1,101)]
tree=StoryNavigationService(q).build({},10);assert len(tree)==2 and sum(len(s.quests) for x in tree for s in x.sections)==100
print("Stage 21.13.6c Story navigation smoke: PASS")
