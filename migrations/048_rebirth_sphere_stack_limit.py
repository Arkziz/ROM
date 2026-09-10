#!/usr/bin/env python3
"""Migration 048: Rebirth Sphere uses the standard consumable stack limit of 10."""
REBIRTH_SPHERE_ITEM_ID=504
MAX_STACK=10
def up(conn):
 row=conn.execute("SELECT id,name FROM items WHERE id=?",(REBIRTH_SPHERE_ITEM_ID,)).fetchone()
 if not row:raise RuntimeError("Rebirth Sphere item 504 is missing")
 conn.execute("UPDATE items SET max_stack=? WHERE id=?",(MAX_STACK,REBIRTH_SPHERE_ITEM_ID))
 reservation_table=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='inventory_reservations'").fetchone()
 if reservation_table:
  reserved=int(conn.execute("""SELECT COUNT(*) FROM inventory_reservations r JOIN inventory i ON i.id=r.inventory_id WHERE i.item_id=?""",(REBIRTH_SPHERE_ITEM_ID,)).fetchone()[0] or 0)
  if reserved:raise RuntimeError(f"Cannot normalize reserved Rebirth Sphere stacks: {reserved}")
 users=conn.execute("SELECT DISTINCT user_id FROM inventory WHERE item_id=? ORDER BY user_id",(REBIRTH_SPHERE_ITEM_ID,)).fetchall()
 normalized=created=deleted=0
 for (user_id,) in users:
  rows=conn.execute("SELECT id,COALESCE(quantity,0) FROM inventory WHERE user_id=? AND item_id=? ORDER BY id",(int(user_id),REBIRTH_SPHERE_ITEM_ID)).fetchall()
  total=sum(max(0,int(r[1] or 0)) for r in rows)
  if not rows:continue
  desired=[];remaining=total
  while remaining>0:
   qty=min(MAX_STACK,remaining);desired.append(qty);remaining-=qty
  if not desired:desired=[0]
  for index,qty in enumerate(desired):
   if index<len(rows):conn.execute("UPDATE inventory SET quantity=? WHERE id=?",(qty,int(rows[index][0])))
   else:
    cols={str(r[1]) for r in conn.execute("PRAGMA table_info(inventory)")};names=["user_id","item_id","quantity"];values=[int(user_id),REBIRTH_SPHERE_ITEM_ID,qty]
    if "durability" in cols:names.append("durability");values.append(None)
    if "max_durability" in cols:names.append("max_durability");values.append(None)
    if "refine_level" in cols:names.append("refine_level");values.append(0)
    conn.execute("INSERT INTO inventory("+",".join(names)+") VALUES("+",".join("?" for _ in names)+")",values);created+=1
  for inventory_id,_quantity in rows[len(desired):]:conn.execute("DELETE FROM inventory WHERE id=?",(int(inventory_id),));deleted+=1
  normalized+=1
 invalid=conn.execute("SELECT COUNT(*) FROM inventory WHERE item_id=? AND (quantity<1 OR quantity>?)",(REBIRTH_SPHERE_ITEM_ID,MAX_STACK)).fetchone()[0]
 if invalid:raise RuntimeError(f"Invalid Rebirth Sphere stacks after migration: {invalid}")
 return {"item_id":REBIRTH_SPHERE_ITEM_ID,"max_stack":MAX_STACK,"normalized_users":normalized,"created_rows":created,"deleted_rows":deleted}
