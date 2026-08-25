import ast,logging,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
for rel in ("systems/production_logging.py","main.py","systems/notifications.py","systems/telegram_rate_limit.py","handlers/combat.py"):
 s=(R/rel).read_text(encoding="utf-8");ast.parse(s);assert s.count("ROM 17.20.1.1 CRITICAL PRODUCTION LOGGING PRINT CONTRACT RECOVERY")==1,rel
from systems.production_logging import configure_production_logging,get_production_logger,get_security_logger,logging_status,redact_log_text,production_log_print
configure_production_logging(force=True);assert len([h for h in logging.getLogger().handlers if getattr(h,"_rom_production_handler",False)])==4
configure_production_logging();assert len([h for h in logging.getLogger().handlers if getattr(h,"_rom_production_handler",False)])==4
x=redact_log_text("BOT_TOKEN=123:ABC authorization=Bearer value password=hidden");assert "123:ABC" not in x and "value" not in x and "hidden" not in x
production_log_print(get_production_logger("smoke"),"info","smoke","info",sep="_");production_log_print(get_production_logger("smoke"),"error","smoke_error","bot_token=123:ABC",flush=True);get_security_logger("smoke").warning("smoke_security user_id=1")
for h in logging.getLogger().handlers:
 try:h.flush()
 except Exception:pass
p=logging_status()["paths"]
for q in p.values():assert Path(q).exists() and "123:ABC" not in Path(q).read_text(encoding="utf-8")
assert "smoke_info" in Path(p["app"]).read_text(encoding="utf-8");assert "smoke_error" in Path(p["error"]).read_text(encoding="utf-8");assert "smoke_security" in Path(p["security"]).read_text(encoding="utf-8")
for rel in ("main.py","systems/notifications.py","systems/telegram_rate_limit.py","handlers/combat.py"):
 t=ast.parse((R/rel).read_text(encoding="utf-8"));assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="print" for n in ast.walk(t)),rel
print("[PASS] Stage 17.20.1.1 critical production logging print contract recovery")
