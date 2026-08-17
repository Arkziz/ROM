from __future__ import annotations
import inspect,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db_modules.inventory as inventory
class FakeCursor:
    def __init__(self,quantity): self.quantity=quantity; self.calls=[]
    def execute(self,sql,args): self.calls.append((" ".join(sql.split()),args)); return self
    def fetchone(self): return (self.quantity,)
class FakeConn:
    def __init__(self): self.commits=0
    def commit(self): self.commits+=1
orig_cursor,orig_conn=inventory.cursor,inventory.conn
try:
    c=FakeCursor(3); co=FakeConn(); inventory.cursor=c; inventory.conn=co
    assert inventory.consume_inventory_item(123,77,1) is True
    assert c.calls[0][1]==(77,123)
    assert c.calls[1][1]==(2,77,123)
    assert co.commits==1
    c=FakeCursor(1); co=FakeConn(); inventory.cursor=c; inventory.conn=co
    assert inventory.consume_inventory_item(77,1) is True
    assert c.calls[1][1]==(77,)
finally:
    inventory.cursor,inventory.conn=orig_cursor,orig_conn
sig=inspect.signature(inventory.consume_inventory_item)
assert list(sig.parameters)==["user_id_or_inventory_id","inventory_id_or_amount","amount"]
print("[PASS] consume inventory dual signature contract")
