#!/usr/bin/env python3
"""Smoke check for Stage 21.11.2c World Graph."""
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from rom_v2.content.location_catalog import LOCATIONS, validate_location_catalog
from rom_v2.content.world_graph import *

def main():
    validate_world_graph(location_ids=set(LOCATIONS))
    validate_location_catalog()
    assert WORLD_NODE_ORDER == ("city", "start_path", "dark_forest")
    assert LOCATION_GRAPH == {"city": ("start_path",), "start_path": ("city", "dark_forest"), "dark_forest": ("start_path",)}
    assert TRAVEL_SECONDS == 20 and TRANSPORT_REQUIREMENTS == ()
    assert get_world_node("missing") is None
    assert get_adjacent_nodes("missing") == ()
    assert not are_adjacent("city", "dark_forest")
    print("Stage 21.11.2c World Graph smoke: PASS")
    return 0
if __name__ == "__main__": raise SystemExit(main())
