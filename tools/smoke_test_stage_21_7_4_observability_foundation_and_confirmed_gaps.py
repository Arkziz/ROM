from pathlib import Path
import importlib.util
module_path=Path(__file__).resolve().parents[1]/"systems"/"production_logging.py"
spec=importlib.util.spec_from_file_location("stage_21_7_4_production_logging",module_path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
normalize_error_category=module.normalize_error_category
new_operation_id=module.new_operation_id
_redact_observability_value=module._redact_observability_value
log_observability_exception=module.log_observability_exception
assert normalize_error_category("migration_failure")=="MIGRATION_FAILURE"
assert normalize_error_category("unknown") == "DOMAIN_FAILURE"
op=new_operation_id("trade");assert op.startswith("trade:") and len(op)>20
safe=_redact_observability_value({"token":"abc","nested":{"password":"pw","value":"ok"}})
assert safe["token"]=="[REDACTED]" and safe["nested"]["password"]=="[REDACTED]" and safe["nested"]["value"]=="ok"
class Capture:
 def __init__(self):self.args=None
 def exception(self,*args,**kwargs):self.args=(args,kwargs)
cap=Capture()
try: raise RuntimeError("boom")
except RuntimeError:
 result=log_observability_exception("WORKER_FAILURE","worker.test",operation_id="op:1",context={"secret":"x"},logger=cap)
assert result=={"category":"WORKER_FAILURE","phase":"worker.test","operation_id":"op:1"}
assert cap.args and "WORKER_FAILURE" in cap.args[0] and cap.args[0][-1]["secret"]=="[REDACTED]"
print("PASS: Stage 21.7.4 category, correlation and redaction smoke")
