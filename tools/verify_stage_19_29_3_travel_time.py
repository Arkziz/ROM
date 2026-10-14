from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.location_graph import TRAVEL_SECONDS,validate_location_graph
assert TRAVEL_SECONDS==20
assert validate_location_graph() is True
print('PASS: Stage 19.29.3')
