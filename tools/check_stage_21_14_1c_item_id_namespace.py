from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.item_id_namespace_service import V2ItemIdNamespaceService
s=V2ItemIdNamespaceService();b=s.allocate_event_block("event");p=s.allocate_preview_id();a=s.plan_preview_promotion(p);assert (b.start_id,b.end_id)==(4000,4024);assert s.plan_preview_promotion(p)==a
print("Stage 21.14.1c item ID namespace smoke: PASS")
