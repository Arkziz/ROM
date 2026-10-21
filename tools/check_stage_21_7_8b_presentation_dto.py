from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.presentation.item_dto import *
x=build_item_description(ItemPresentationInput(1,2,"Item",primary_stats={"str":1}))
assert x.item_id==1 and x.inventory_id==2 and x.fields[-1].key=="str"
assert not any(name in globals() for name in ("commit","update","calculate_price"))
print("[PASS] Stage 21.7.8b presentation DTO contract")
