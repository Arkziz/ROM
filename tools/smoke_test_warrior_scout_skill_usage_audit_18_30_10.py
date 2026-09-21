from __future__ import annotations
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from tools.audit_warrior_scout_skill_usage import run_audit
x=run_audit();assert x['status']=='PASS' and x['gameplay_changed'] is False;w=next(i for i in x['dynamic_action_audit'] if i['class']=='warrior');s=next(i for i in x['dynamic_action_audit'] if i['class']=='scout');assert w['action_counts'].get('warrior_subjugation_strike',0)==0;assert s['action_counts'].get('scout_sting_arrow',0)==0
print('[PASS] deterministic warrior/scout skill selection audit fixture')
