# -*- coding: utf-8 -*-
"""Stage 18.1.9a: migrate permanent generated equipment to 10000+."""
from datetime import datetime, timezone
from systems.item_id_allocator_system import init_item_id_allocator_system, record_item_id_mapping
DIRECT_COLUMNS=(("auction_lots","item_ref_id"),("character_name_changes","item_id"),("crystal_shop_purchases","item_id"),("inventory","item_id"),("inventory_runes","rune_item_id"),("player_trade_offers","item_id"),("premium_item_grants","item_id"),("refine_attempts","item_id"))
def _columns(conn,table): return {str(r[1]) for r in conn.execute('PRAGMA table_info("'+table+'")')}
def migrate(conn):
    rows=conn.execute("SELECT id FROM items WHERE is_generated=1 AND shop_preview_owner IS NULL AND COALESCE(shop_preview_price,0)=0 ORDER BY id").fetchall()
    old=[int(r[0]) for r in rows if int(r[0])>=50001 and int(r[0])<1000000]
    if not old:
        init_item_id_allocator_system(conn=conn); return {"success":True,"already_migrated":True}
    targets=list(range(10000,10000+len(old)))
    occupied=conn.execute("SELECT id FROM items WHERE id IN ("+','.join('?' for _ in targets)+")",targets).fetchall()
    if occupied: raise RuntimeError("Generated migration targets are occupied")
    init_item_id_allocator_system(conn=conn)
    fk=conn.execute("PRAGMA foreign_keys").fetchone()[0]; conn.execute("PRAGMA foreign_keys=OFF")
    try:
        for old_id,new_id in zip(old,targets):
            temporary=920000000+old_id
            conn.execute("UPDATE items SET id=? WHERE id=?",(temporary,old_id))
            for table,column in DIRECT_COLUMNS:
                if column in _columns(conn,table): conn.execute(f'UPDATE "{table}" SET "{column}"=? WHERE "{column}"=?',(temporary,old_id))
            conn.execute("UPDATE items SET id=? WHERE id=?",(new_id,temporary))
            for table,column in DIRECT_COLUMNS:
                if column in _columns(conn,table): conn.execute(f'UPDATE "{table}" SET "{column}"=? WHERE "{column}"=?',(new_id,temporary))
            record_item_id_mapping(conn,old_id,new_id,"initial_namespace_migration","18.1.9a")
        init_item_id_allocator_system(conn=conn)
        conn.execute("UPDATE item_id_allocator SET last_issued_id=? WHERE namespace='generated_equipment'",(targets[-1],))
        return {"success":True,"migrated":len(old),"first":targets[0],"last":targets[-1]}
    finally:
        conn.execute(f"PRAGMA foreign_keys={int(fk)}")
def run(conn): return migrate(conn)
