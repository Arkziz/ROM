from __future__ import annotations
import ast, sqlite3, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for rel in ('systems/pve_auto_escape_system.py','handlers/combat.py','main.py'):
 ast.parse((ROOT/rel).read_text(encoding='utf-8-sig'))
s=(ROOT/'systems/pve_auto_escape_system.py').read_text(encoding='utf-8-sig'); c=(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig'); m=(ROOT/'main.py').read_text(encoding='utf-8-sig')
assert 'PVE_AUTO_ESCAPE_TIMEOUT_SECONDS = 300' in s
assert 'BEGIN IMMEDIATE' in s and "status='active'" in s
assert 'process_victory' in c and "claim_pve_terminal(user_id, 'victory'" in c
assert 'begin_pve_encounter(' in c and "claim_pve_terminal(user_id, 'manual_escape'" in c
assert 'recover_pve_encounters_after_restart(bot)' in m and 'start_pve_auto_escape_worker(bot)' in m
assert 'game.db-wal' not in s+c+m and 'game.db-shm' not in s+c+m
print('[PASS] Stage 18.18.1 PvE auto-escape production contracts')
