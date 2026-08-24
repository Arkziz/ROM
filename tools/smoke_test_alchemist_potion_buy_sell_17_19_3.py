import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
for rel in ("systems/potion_system.py","handlers/city.py"):
 s=(R/rel).read_text(encoding="utf-8");ast.parse(s);assert s.count("ROM 17.19.3 ALCHEMIST POTION BUY SELL")>=1,rel
from systems.potion_system import buy_alchemist_potion_17_19_3,sell_alchemist_potion_17_19_3,get_alchemist_potion_stock_17_19_3
import handlers.city as c
for n in ("build_alchemist_root_17_19_3","build_alchemist_buy_preview_17_19_3","build_alchemist_sell_preview_17_19_3"):
 assert hasattr(c,n),n
assert "alchemist:buy" in (R/"handlers/city.py").read_text(encoding="utf-8")
assert "alchemist:sell" in (R/"handlers/city.py").read_text(encoding="utf-8")
print("[PASS] Stage 17.19.3 Alchemist potion buy/sell contract")
