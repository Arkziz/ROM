from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from rom_v2.domain.npc_dialogue_model import V2NpcDefinition
from rom_v2.application.npc_dialogue_service import InMemoryV2NpcRegistry,InMemoryV2QuestNpcPort,V2NpcDialogueService
s=V2NpcDialogueService(InMemoryV2NpcRegistry((V2NpcDefinition("n","NPC","l"),)),InMemoryV2QuestNpcPort());assert s.view("n","l").ok
print("Stage 21.13.3c NPC/dialogue model smoke: PASS")
