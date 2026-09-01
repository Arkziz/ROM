# -*- coding: utf-8 -*-
"""Canonical never-reuse item ID allocator for generated equipment and previews."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone

PRIMARY_MIN=10000
PRIMARY_MAX=5009999
OVERFLOW_MIN=5010000
OVERFLOW_MAX=10009999
PREVIEW_MIN=10010000
PREVIEW_MAX=11009999
PERMANENT_NAMESPACE="generated_equipment"
PREVIEW_NAMESPACE="shop_preview"

class ItemIdPoolExhausted(RuntimeError):
    pass

def init_item_id_allocator_system(db_path=None, conn=None):
    own=conn is None
    if own: conn=sqlite3.connect(db_path or "game.db")
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS item_id_allocator(
            namespace TEXT PRIMARY KEY,last_issued_id INTEGER NOT NULL,
            range_min INTEGER NOT NULL,range_max INTEGER NOT NULL,
            updated_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS generated_item_id_migrations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,source_item_id INTEGER NOT NULL,
            target_item_id INTEGER NOT NULL UNIQUE,operation TEXT NOT NULL,
            migration_stage TEXT NOT NULL,created_at TEXT NOT NULL,
            UNIQUE(source_item_id,target_item_id,operation))""")
        now=datetime.now(timezone.utc).isoformat()
        permanent_max=conn.execute("SELECT COALESCE(MAX(id),?) FROM items WHERE is_generated=1 AND shop_preview_owner IS NULL AND COALESCE(shop_preview_price,0)=0 AND id BETWEEN ? AND ?",(PRIMARY_MIN-1,PRIMARY_MIN,OVERFLOW_MAX)).fetchone()[0]
        preview_max=conn.execute("SELECT COALESCE(MAX(id),?) FROM items WHERE (shop_preview_owner IS NOT NULL OR COALESCE(shop_preview_price,0)>0) AND id BETWEEN ? AND ?",(PREVIEW_MIN-1,PREVIEW_MIN,PREVIEW_MAX)).fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO item_id_allocator(namespace,last_issued_id,range_min,range_max,updated_at) VALUES(?,?,?,?,?)",(PERMANENT_NAMESPACE,max(PRIMARY_MIN-1,int(permanent_max)),PRIMARY_MIN,OVERFLOW_MAX,now))
        conn.execute("INSERT OR IGNORE INTO item_id_allocator(namespace,last_issued_id,range_min,range_max,updated_at) VALUES(?,?,?,?,?)",(PREVIEW_NAMESPACE,max(PREVIEW_MIN-1,int(preview_max)),PREVIEW_MIN,PREVIEW_MAX,now))
        if own: conn.commit()
        return {"success":True}
    finally:
        if own: conn.close()

def _allocate(conn,namespace):
    init_item_id_allocator_system(conn=conn)
    row=conn.execute("SELECT last_issued_id,range_min,range_max FROM item_id_allocator WHERE namespace=?",(namespace,)).fetchone()
    if not row: raise RuntimeError("Allocator namespace is not initialized")
    next_id=max(int(row[0])+1,int(row[1]))
    if next_id>int(row[2]): raise ItemIdPoolExhausted(f"Item ID pool exhausted: {namespace}")
    if conn.execute("SELECT 1 FROM items WHERE id=?",(next_id,)).fetchone(): raise RuntimeError(f"Allocator collision at {next_id}")
    conn.execute("UPDATE item_id_allocator SET last_issued_id=?,updated_at=? WHERE namespace=?",(next_id,datetime.now(timezone.utc).isoformat(),namespace))
    return next_id

def allocate_generated_item_id(conn):
    return _allocate(conn,PERMANENT_NAMESPACE)

def allocate_shop_preview_item_id(conn):
    return _allocate(conn,PREVIEW_NAMESPACE)

def record_item_id_mapping(conn,source_item_id,target_item_id,operation,migration_stage):
    conn.execute("INSERT OR IGNORE INTO generated_item_id_migrations(source_item_id,target_item_id,operation,migration_stage,created_at) VALUES(?,?,?,?,?)",(int(source_item_id),int(target_item_id),str(operation),str(migration_stage),datetime.now(timezone.utc).isoformat()))

def promote_shop_preview_item(conn,preview_item_id):
    preview_item_id=int(preview_item_id)
    row=conn.execute("SELECT * FROM items WHERE id=? AND shop_preview_owner IS NOT NULL AND COALESCE(shop_preview_price,0)>0",(preview_item_id,)).fetchone()
    if not row: raise RuntimeError("Shop preview item not found")
    columns=[str(r[1]) for r in conn.execute("PRAGMA table_info(items)")]
    target=allocate_generated_item_id(conn)
    values=list(row); values[columns.index("id")]=target
    if "shop_preview_owner" in columns: values[columns.index("shop_preview_owner")]=None
    if "shop_preview_price" in columns: values[columns.index("shop_preview_price")]=0
    conn.execute("INSERT INTO items("+",".join('"'+c+'"' for c in columns)+") VALUES("+",".join('?' for _ in columns)+")",values)
    record_item_id_mapping(conn,preview_item_id,target,"shop_preview_purchase","18.1.9a")
    return target
