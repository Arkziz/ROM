from __future__ import annotations
import inspect,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from db import get_inventory_entry
sig=inspect.signature(get_inventory_entry)
assert list(sig.parameters)==["user_id_or_inventory_id","inventory_id"]
assert sig.parameters["inventory_id"].default is None
import db_modules.equipment as equipment
class FakeConn:
    def __init__(self,row): self.row=row; self.args=None
    def execute(self,sql,args): self.args=(sql,args); return self
    def fetchone(self): return self.row
original_conn=equipment.conn
original_format=equipment.format_refined_item_name
try:
    fake=FakeConn((77,201,"Мале зілля здоров'я","potion_hp","potion",3,0))
    equipment.conn=fake
    equipment.format_refined_item_name=lambda name,level:name if not level else f"{name} [+{level}]"
    value=equipment.get_inventory_entry(123,77)
    assert value==(77,201,"Мале зілля здоров'я","potion_hp","potion",3),value
    assert fake.args[1]==(123,77)
finally:
    equipment.conn=original_conn
    equipment.format_refined_item_name=original_format
print("[PASS] inventory entry dual signature contract")
