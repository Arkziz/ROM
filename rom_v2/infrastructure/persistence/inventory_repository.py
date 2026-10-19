"""SQLite adapter for item definitions and owned inventory rows."""
from __future__ import annotations
import json, sqlite3
from rom_v2.domain.item import ItemDefinition, ItemInstance

class SQLiteInventoryRepository:
    def __init__(self,connection:sqlite3.Connection): self._connection=connection
    def get_definition(self,item_id:int):
        row=self._connection.execute("SELECT item_id,name,item_type,metadata_json FROM item_definitions WHERE item_id=?",(item_id,)).fetchone()
        return None if row is None else ItemDefinition(int(row[0]),str(row[1]),str(row[2]),json.loads(row[3]))
    def list_by_owner(self,owner_user_id:int):
        rows=self._connection.execute("SELECT inventory_id,owner_user_id,item_id,quantity,instance_metadata_json FROM inventory_items WHERE owner_user_id=? ORDER BY inventory_id",(owner_user_id,)).fetchall()
        return tuple(ItemInstance(int(r[0]),int(r[1]),int(r[2]),int(r[3]),json.loads(r[4])) for r in rows)
    def get_instance(self,owner_user_id:int,inventory_id:int):
        r=self._connection.execute("SELECT inventory_id,owner_user_id,item_id,quantity,instance_metadata_json FROM inventory_items WHERE owner_user_id=? AND inventory_id=?",(owner_user_id,inventory_id)).fetchone()
        return None if r is None else ItemInstance(int(r[0]),int(r[1]),int(r[2]),int(r[3]),json.loads(r[4]))
    def insert_instance(self,owner_user_id:int,item_id:int,quantity:int):
        cur=self._connection.execute("INSERT INTO inventory_items(owner_user_id,item_id,quantity,instance_metadata_json) VALUES(?,?,?,'{}')",(owner_user_id,item_id,quantity))
        return ItemInstance(int(cur.lastrowid),owner_user_id,item_id,quantity,{})
    def change_quantity(self,inventory_id:int,quantity:int): self._connection.execute("UPDATE inventory_items SET quantity=? WHERE inventory_id=?",(quantity,inventory_id))
    def delete_instance(self,inventory_id:int): self._connection.execute("DELETE FROM inventory_items WHERE inventory_id=?",(inventory_id,))
