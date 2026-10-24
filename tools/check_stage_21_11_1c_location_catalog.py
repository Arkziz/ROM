#!/usr/bin/env python3
"""Smoke check for Stage 21.11.1c Location Catalog."""
from pathlib import Path
import sys

# Direct execution sets sys.path[0] to ROM/tools. Add the project root so the
# repository-local rom_v2 package resolves without installation or PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rom_v2.content.location_catalog import *

def main():
    validate_location_catalog()
    assert LOCATION_ORDER == ("start_path","dark_forest") and len(LOCATIONS)==2
    assert get_location_display_name("start_path") == "🌿 Початок Шляху"
    assert get_location_display_name("dark_forest") == "🌲 Темний Бір"
    assert tuple(x.location_id for x in get_unlocked_locations(5)) == ("start_path",)
    assert tuple(x.location_id for x in get_unlocked_locations(6)) == ("start_path","dark_forest")
    assert LOCATION_GRAPH == {"city":("start_path",),"start_path":("city","dark_forest"),"dark_forest":("start_path",)}
    try: require_location("third_location")
    except KeyError: pass
    else: raise AssertionError("unknown location did not fail closed")
    print("Stage 21.11.1c Location Catalog smoke: PASS")
    return 0
if __name__ == "__main__": raise SystemExit(main())
