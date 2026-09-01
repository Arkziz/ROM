# -*- coding: utf-8 -*-
"""Stage 18.1.9b: recover permanent inventory items stranded in preview namespace."""
from systems.item_id_allocator_system import recover_stranded_preview_item

def migrate(conn):
    rows=conn.execute("""SELECT DISTINCT it.id FROM items it JOIN inventory inv ON inv.item_id=it.id
        WHERE it.id BETWEEN 10010000 AND 11009999
          AND it.shop_preview_owner IS NULL AND COALESCE(it.shop_preview_price,0)=0
        ORDER BY it.id""").fetchall()
    recovered=[]
    for row in rows:
        source=int(row[0]); target=recover_stranded_preview_item(conn,source)
        recovered.append({"source_item_id":source,"target_item_id":target})
    return {"success":True,"recovered":recovered,"count":len(recovered)}

def run(conn): return migrate(conn)
