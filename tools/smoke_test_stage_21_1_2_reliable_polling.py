#!/usr/bin/env python3
import ast
from pathlib import Path
s=Path(__file__).resolve().parents[1]/"main.py"; tree=ast.parse(s.read_text(encoding="utf-8-sig"))
keep={"_is_transient_polling_error","_polling_retry_delay","run_bot_polling_resilient"}; body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.Assign)) and (getattr(n,"name",None) in keep or any(getattr(t,"id","").startswith("_ROM_POLLING_BACKOFF_") for t in getattr(n,"targets",[])))]
mod=ast.Module(body=body,type_ignores=[]); ns={"_rom_polling_requests":None,"_rom_polling_random":__import__("random"),"_rom_polling_time":__import__("time"),"PRODUCTION_LOG_PRINT":lambda *a,**k:None,"PRODUCTION_LOGGER":None}; exec(compile(ast.fix_missing_locations(mod),"main.py","exec"),ns)
class Transient(Exception): pass
class Bot:
 def __init__(self,errors): self.errors=list(errors); self.calls=0
 def infinity_polling(self):
  self.calls+=1
  if self.errors: raise self.errors.pop(0)
d=[]; b=Bot([TimeoutError("timed out"),TimeoutError("timed out")]); ns["run_bot_polling_resilient"](b,sleep_fn=d.append,random_uniform=lambda a,b:0.0); assert b.calls==3 and d==[2.0,4.0]
b=Bot([ValueError("fatal")]);
try: ns["run_bot_polling_resilient"](b,sleep_fn=lambda x:None,random_uniform=lambda a,b:0.0)
except ValueError: pass
else: raise AssertionError("fatal error swallowed")
assert ns["_polling_retry_delay"](99,random_uniform=lambda a,b:1.0)==30.0
print("PASS: Stage 21.1.2 isolated no-network polling smoke")
