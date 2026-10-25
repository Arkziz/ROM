from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from rom_v2.domain.quest_item_store import V2QuestItemBalanceKey,V2QuestItemCollection
from rom_v2.application.quest_item_store_service import InMemoryV2QuestItemStoreUow,V2QuestItemStoreService
u=InMemoryV2QuestItemStoreUow();s=V2QuestItemStoreService(u);k=V2QuestItemBalanceKey(1,1,"item");assert s.collect(V2QuestItemCollection(k,"event",1)).ok;assert s.quantity(k)==1
print("Stage 21.13.2c Quest Item Store smoke: PASS")
