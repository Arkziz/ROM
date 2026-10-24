#!/usr/bin/env python3
from pathlib import Path
import sys
from datetime import datetime,timedelta,timezone
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.travel_service import *
from rom_v2.domain.travel_aggregate import TravelStatus
n=datetime(2026,1,1,tzinfo=timezone.utc);u=MemoryUow({1:{"location":"city","level":6}});s=TravelService(u,MemoryBusy());t=s.start(1,"start_path",n).travel;r=s.complete(t.travel_id,n+timedelta(seconds=20));assert r.success and r.travel.status is TravelStatus.ARRIVED;print("Stage 21.11.3c Travel Aggregate smoke: PASS")
