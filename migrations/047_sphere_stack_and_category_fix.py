#!/usr/bin/env python3
"""Migration 047: stack Rebirth Spheres and make both spheres consumable-only."""
REBIRTH_SPHERE_ITEM_ID=504
NEW_PATH_SPHERE_ITEM_ID=501
REBIRTH_MAX_STACK=99
def up(conn):
 rows=conn.execute("SELECT id,name FROM items WHERE id IN (?,?) ORDER BY id",(NEW_PATH_SPHERE_ITEM_ID,REBIRTH_SPHERE_ITEM_ID)).fetchall()
 if [int(r[0]) for r in rows] != [501,504]:raise RuntimeError(f"Sphere items missing: {rows}")
 conn.execute("UPDATE items SET category='consumable' WHERE id IN (?,?)",(NEW_PATH_SPHERE_ITEM_ID,REBIRTH_SPHERE_ITEM_ID))
 conn.execute("UPDATE items SET max_stack=? WHERE id=?",(REBIRTH_MAX_STACK,REBIRTH_SPHERE_ITEM_ID))
 reservation_table=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='inventory_reservations'").fetchone()
 if reservation_table:
  reserved=conn.execute("""SELECT COUNT(*) FROM inventory_reservations r JOIN inventory i ON i.id=r.inventory_id WHERE i.item_id=?""",(REBIRTH_SPHERE_ITEM_ID,)).fetchone()[0]
  if int(reserved or 0)>0:raise RuntimeError(f"Cannot normalize reserved Rebirth Sphere stacks: {reserved}")
 users=conn.execute("SELECT DISTINCT user_id FROM inventory WHERE item_id=? ORDER BY user_id",(REBIRTH_SPHERE_ITEM_ID,)).fetchall()
 normalized_users=removed_rows=0
 for (user_id,) in users:
  stacks=conn.execute("SELECT id,COALESCE(quantity,0) FROM inventory WHERE user_id=? AND item_id=? ORDER BY id",(int(user_id),REBIRTH_SPHERE_ITEM_ID)).fetchall()
  total=sum(max(0,int(r[1] or 0)) for r in stacks)
  if not stacks:continue
  first=int(stacks[0][0]);conn.execute("UPDATE inventory SET quantity=? WHERE id=?",(total,first))
  for inventory_id,_quantity in stacks[1:]:conn.execute("DELETE FROM inventory WHERE id=?",(int(inventory_id),));removed_rows+=1
  normalized_users+=1
 duplicates=conn.execute("""SELECT COUNT(*) FROM (SELECT user_id FROM inventory WHERE item_id=? GROUP BY user_id HAVING COUNT(*)>1)""",(REBIRTH_SPHERE_ITEM_ID,)).fetchone()[0]
 if duplicates:raise RuntimeError(f"Rebirth Sphere duplicate stacks remain: {duplicates}")
 return {"normalized_users":normalized_users,"removed_rows":removed_rows,"max_stack":REBIRTH_MAX_STACK}
