"""Presentation helpers for V2 overlevel reconciliation."""
from __future__ import annotations
from rom_v2.domain.overlevel_policy import OverlevelReconciliationResult
LOCATION_NAMES={"start_path":"Початок Шляху","dark_forest":"Темний Бір"}
def build_overlevel_message(result:OverlevelReconciliationResult)->str|None:
 lines=[]
 for item in result.locations:
  if item.skipped_now>0:lines.append(f"{LOCATION_NAMES[item.location_id]}: пропущено без нагород: {item.skipped_now}")
 return "\n".join(lines) if lines else None
