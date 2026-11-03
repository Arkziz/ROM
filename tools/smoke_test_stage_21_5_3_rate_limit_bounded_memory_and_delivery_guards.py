import importlib.util, sys, types
from pathlib import Path
# Isolated future-source import: stub only the production logger dependency.
systems_pkg=types.ModuleType("systems")
systems_pkg.__path__=[]
sys.modules["systems"]=systems_pkg
logging_mod=types.ModuleType("systems.production_logging")
logging_mod.get_production_logger=lambda name: object()
logging_mod.production_log_print=lambda *args, **kwargs: None
sys.modules["systems.production_logging"]=logging_mod
p=Path("systems/telegram_rate_limit.py")
spec=importlib.util.spec_from_file_location("stage_21_5_3_future_telegram_rate_limit",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
with m._LOCK:
 m._BLOCKED_UNTIL_BY_CHAT.clear(); m._SUPPRESSED_COUNTS.clear(); m._STATE_LAST_UPDATED.clear()
 now=1000.0
 m._BLOCKED_UNTIL_BY_CHAT[1]=now+100
 for i in range(5000):
  key=("send_message",i+2); m._SUPPRESSED_COUNTS[key]=1; m._STATE_LAST_UPDATED[key]=now-7200
 sizes=m._cleanup_rate_limit_state_locked(now)
 assert 1 in m._BLOCKED_UNTIL_BY_CHAT
 assert sizes["suppressed"] <= m._STATE_MAX_ENTRIES
 assert sizes["blocked"] <= m._STATE_MAX_ENTRIES
print("PASS: Stage 21.5.3 preserves active cooldown and bounds 5000 chat keys")
