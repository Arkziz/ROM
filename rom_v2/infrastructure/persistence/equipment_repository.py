"""SQLite equipment repository bound to exact inventory_items.inventory_id."""
from __future__ import annotations
import json,sqlite3
from rom_v2.domain.equipment import EquipmentSlot
from rom_v2.domain.item import ItemInstance
class SQLiteEquipmentRepository:
 def __init__(self,connection:sqlite3.Connection):self._connection=connection
 def list_slots(self,owner_user_id:int):
  rows=self._connection.execute("SELECT owner_user_id,slot_key,inventory_id FROM equipment_slots WHERE owner_user_id=? ORDER BY CASE slot_key WHEN 'main_hand' THEN 1 WHEN 'off_hand' THEN 2 WHEN 'helmet' THEN 3 WHEN 'shoulders' THEN 4 WHEN 'chest' THEN 5 WHEN 'gloves' THEN 6 WHEN 'legs' THEN 7 WHEN 'boots' THEN 8 WHEN 'necklace' THEN 9 WHEN 'ring' THEN 10 END",(owner_user_id,)).fetchall()
  return tuple(EquipmentSlot(int(r[0]),str(r[1]),int(r[2])) for r in rows)
 def get_inventory_instance(self,owner_user_id:int,inventory_id:int):
  r=self._connection.execute("SELECT inventory_id,owner_user_id,item_id,quantity,instance_metadata_json FROM inventory_items WHERE owner_user_id=? AND inventory_id=?",(owner_user_id,inventory_id)).fetchone()
  return None if r is None else ItemInstance(int(r[0]),int(r[1]),int(r[2]),int(r[3]),json.loads(r[4]))
 def set_slot(self,owner_user_id:int,slot_key:str,inventory_id:int):
  self._connection.execute("INSERT INTO equipment_slots(owner_user_id,slot_key,inventory_id) VALUES(?,?,?) ON CONFLICT(owner_user_id,slot_key) DO UPDATE SET inventory_id=excluded.inventory_id",(owner_user_id,slot_key,inventory_id))
 def clear_slot(self,owner_user_id:int,slot_key:str):self._connection.execute("DELETE FROM equipment_slots WHERE owner_user_id=? AND slot_key=?",(owner_user_id,slot_key))
