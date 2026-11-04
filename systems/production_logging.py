# -*- coding: utf-8 -*-
# ROM 17.20.1.1 CRITICAL PRODUCTION LOGGING PRINT CONTRACT RECOVERY
from __future__ import annotations
import builtins, logging, os, re, sys, threading
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
_LOCK=threading.RLock();_CONFIGURED=False
_ROOT=Path(__file__).resolve().parents[1];_LOG_ROOT=_ROOT/"logs"
_PATTERNS=(
 re.compile(r"(?i)(bot[_-]?token|telegram[_-]?token|api[_-]?token)(\s*[:=]\s*)([^\s,;]+)"),
 re.compile(r"(?i)(authorization)(\s*[:=]\s*)(?:bearer\s+)?([^\s,;]+)"),
 re.compile(r"(?i)(password|passwd|pwd|secret|private[_-]?key|session[_-]?token|auth[_-]?key)(\s*[:=]\s*)([^\s,;]+)"),
 re.compile(r"(?i)bearer\s+[a-z0-9._~+\-/]+=*"),
)
def redact_log_text(value):
 text=str(value)
 for i,p in enumerate(_PATTERNS):
  if i==3:text=p.sub("Bearer [REDACTED]",text)
  else:text=p.sub(lambda m:f"{m.group(1)}{m.group(2)}[REDACTED]",text)
 return text
class RedactingFormatter(logging.Formatter):
 def format(self,record):return redact_log_text(super().format(record))
class MaxLevel(logging.Filter):
 def __init__(self,n):super().__init__();self.n=n
 def filter(self,r):return r.levelno<=self.n
class SecurityOnly(logging.Filter):
 def filter(self,r):return r.name=="rom.security" or r.name.startswith("rom.security.")
class NonSecurity(logging.Filter):
 def filter(self,r):return not (r.name=="rom.security" or r.name.startswith("rom.security."))
def _level():
 x=str(os.getenv("ROM_LOG_LEVEL","INFO")).strip().upper();return getattr(logging,x,logging.INFO) if x in {"DEBUG","INFO","WARNING","ERROR","CRITICAL"} else logging.INFO
def _handler(path,level,days):
 path.parent.mkdir(parents=True,exist_ok=True);h=TimedRotatingFileHandler(path,when="midnight",interval=1,backupCount=days,encoding="utf-8",delay=True);h.setLevel(level);h.suffix="%Y-%m-%d";return h
def configure_production_logging(force=False):
 global _CONFIGURED
 with _LOCK:
  root=logging.getLogger()
  if _CONFIGURED and not force:return logging_status()
  if force:
   for h in list(root.handlers):
    if getattr(h,"_rom_production_handler",False):root.removeHandler(h);h.close()
  _LOG_ROOT.mkdir(parents=True,exist_ok=True);level=_level();fmt=RedactingFormatter("%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(threadName)s | %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
  console=logging.StreamHandler();console.setLevel(level);console.setFormatter(fmt);console.addFilter(NonSecurity())
  app=_handler(_LOG_ROOT/"log"/"rom.log",level,14);app.setFormatter(fmt);app.addFilter(NonSecurity());app.addFilter(MaxLevel(logging.WARNING))
  error=_handler(_LOG_ROOT/"error"/"rom_error.log",logging.ERROR,30);error.setFormatter(fmt);error.addFilter(NonSecurity())
  security=_handler(_LOG_ROOT/"security"/"rom_security.log",logging.INFO,30);security.setFormatter(fmt);security.addFilter(SecurityOnly())
  for h in (console,app,error,security):h._rom_production_handler=True;root.addHandler(h)
  root.setLevel(logging.DEBUG);logging.captureWarnings(True);_CONFIGURED=True
  logging.getLogger("rom.logging").info("production_logging_configured level=%s retention=14/30/30",logging.getLevelName(level));return logging_status()
def logging_status():
 return {"configured":_CONFIGURED,"level":logging.getLevelName(_level()),"paths":{"app":str(_LOG_ROOT/"log"/"rom.log"),"error":str(_LOG_ROOT/"error"/"rom_error.log"),"security":str(_LOG_ROOT/"security"/"rom_security.log")},"retention_days":{"app":14,"error":30,"security":30}}
def get_production_logger(name):
 if not _CONFIGURED:configure_production_logging()
 name=str(name or "rom");return logging.getLogger(name if name=="rom" or name.startswith("rom.") else "rom."+name)
def get_security_logger(subsystem="audit"):
 if not _CONFIGURED:configure_production_logging()
 return logging.getLogger("rom.security."+str(subsystem or "audit").replace(" ","_"))
def production_log_print(logger, log_level, *values, sep=" ", end="\n", file=None, flush=False):
 if file not in (None, sys.stdout, sys.stderr):
  builtins.print(*values, sep=sep, end=end, file=file, flush=flush);return
 message=str(sep).join(str(value) for value in values)
 if end not in (None, "", "\n"):
  message += str(end)
 method=getattr(logger, str(log_level or "info").lower(), logger.info)
 method(message)
 if flush:
  for handler in logging.getLogger().handlers:
   try:handler.flush()
   except Exception:pass

# Stage 21.7.4: stable observability foundation.
OBSERVABILITY_ERROR_CATEGORIES = frozenset({
    "STARTUP_FAILURE", "MIGRATION_FAILURE", "DOMAIN_FAILURE",
    "DELIVERY_FAILURE", "WORKER_FAILURE", "VALIDATION_FAILURE",
})

def normalize_error_category(value):
    category = str(value or "DOMAIN_FAILURE").strip().upper()
    if category not in OBSERVABILITY_ERROR_CATEGORIES:
        return "DOMAIN_FAILURE"
    return category

def new_operation_id(prefix="op"):
    import uuid
    safe_prefix = re.sub(r"[^a-z0-9_.-]+", "_", str(prefix or "op").lower()).strip("_") or "op"
    return f"{safe_prefix}:{uuid.uuid4().hex}"

def _redact_observability_value(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            key_text = str(key)
            if re.search(r"(?i)(token|password|passwd|pwd|secret|authorization|private[_-]?key|payload|email|phone)", key_text):
                cleaned[key_text] = "[REDACTED]"
            else:
                cleaned[key_text] = _redact_observability_value(item)
        return cleaned
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_redact_observability_value(item) for item in value]
    return redact_log_text(value)

def log_observability_exception(category, phase, operation_id=None, context=None, logger=None):
    category = normalize_error_category(category)
    phase = re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(phase or "unknown"))[:120]
    operation_id = str(operation_id or new_operation_id(category.lower()))[:160]
    safe_context = _redact_observability_value(context or {})
    active_logger = logger or get_production_logger("observability")
    active_logger.exception(
        "operation_failed category=%s phase=%s operation_id=%s context=%s",
        category, phase, operation_id, safe_context,
    )
    return {"category": category, "phase": phase, "operation_id": operation_id}

