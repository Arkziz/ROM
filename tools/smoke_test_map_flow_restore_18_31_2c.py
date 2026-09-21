#!/usr/bin/env python3
import ast,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def show(path):
 p=subprocess.run(['git','show','a3395e632aa7ef0214b76c5ed0fb5b2d90d8bf4e'+':'+path],cwd=R,text=True,capture_output=True)
 assert p.returncode==0,p.stderr
 return p.stdout
base_main=show('main.py');base_map=show('handlers/map.py')
main=(R/'main.py').read_text(encoding='utf-8');mp=(R/'handlers/map.py').read_text(encoding='utf-8');travel=(R/'systems/travel_system.py').read_text(encoding='utf-8')
# Dispatch and registration are byte-for-byte restored from the proven checkpoint.
assert main==base_main
# The original working acknowledgement/handler flow is deliberately retained.
assert '🗺️ Мапу відкрито.' in mp
assert '🗺️ Мапу відкрито.' in base_map
# No experimental handlers from 18.31.2a/2b remain.
assert '_open_world_map_from_reply_keyboard_18_31_2a' not in mp
assert '_open_world_map_reply_button_18_31_2b' not in mp
# Text-only normalization remains.
joined=mp+'\n'+travel
for text in ['📍 Поточна локація:','Доступні напрямки:','Поточна локація зміниться лише після завершення подорожі.','Пункт призначення стане поточною локацією після прибуття.','Ти прибув у локацію:']:
 assert text in joined,text
for text in ['📍 Поточне місцезнаходження:','Доступний напрямок:','Ти прибув у:']:
 assert text not in joined,text
ast.parse(mp);ast.parse(travel)
print('[PASS] proven Map flow restored; only wording normalization retained')
