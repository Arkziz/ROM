#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.map_presentation import *
v=build_map_view("start_path",5);assert v.current_label=="🌿 Початок Шляху" and [x.node_id for x in v.directions]==["city","dark_forest"] and not v.directions[1].unlocked;assert decode_callback("map:preview:start_path").node_id=="start_path";assert "start_path" not in " ".join([v.current_label,*[d.label for d in v.directions]]);print("Stage 21.11.4c Map Presentation smoke: PASS")
