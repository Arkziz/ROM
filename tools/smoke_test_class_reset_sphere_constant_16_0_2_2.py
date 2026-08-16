from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.classes import CLASS_RESET_SPHERE_ITEM_ID as canonical
from db import CLASS_RESET_SPHERE_ITEM_ID as compatibility
assert canonical==301,canonical
assert compatibility==canonical,(compatibility,canonical)
print("[PASS] CLASS_RESET_SPHERE_ITEM_ID compatibility export",compatibility)
