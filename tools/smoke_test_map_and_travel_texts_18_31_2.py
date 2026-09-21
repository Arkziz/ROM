#!/usr/bin/env python3
import importlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
for module in ['handlers.map', 'systems.travel_system']:importlib.import_module(module)
sources=[(ROOT/p).read_text(encoding='utf-8') for p in ['handlers/map.py', 'systems/travel_system.py']]
source=chr(10).join(sources)
for stale in ['📍 Поточне місцезнаходження:', 'Доступний напрямок:', 'Місцезнаходження зміниться тільки після завершення подорожі.', 'Поточне місцезнаходження зміниться лише після прибуття.', 'Ти прибув у:', '🗺️ Мапу відкрито.']:assert stale not in source,stale
for current in ['📍 Поточна локація:', 'Доступні напрямки:', 'Поточна локація зміниться лише після завершення подорожі.', 'Пункт призначення стане поточною локацією після прибуття.', 'Ти прибув у локацію:', '🗺️ Мапа світу']:assert current in source,current
assert '✅ Подорож завершено' in source
assert 'Ти прибув у локацію:' in source
print('[PASS] map/travel text owners compile, import, and contain normalized wording')
