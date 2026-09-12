"""Persistent, server-authoritative travel domain for Stage 18.22.1."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from data.location_graph import CITY_NODE, TRAVEL_SECONDS, WORLD_NODES, are_adjacent
from data.locations import is_location_unlocked

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH=ROOT/'game.db'
ACTIVE='active'; TERMINAL=('arrived','cancelled','failed')

def _connect(db_path=None):
    conn=sqlite3.connect(str(db_path or DEFAULT_DB_PATH), timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def _utc(now=None):
    value=now or datetime.now(timezone.utc)
    if value.tzinfo is None: value=value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def _iso(value): return _utc(value).isoformat(timespec='seconds')
def _row(row): return dict(row) if row else None

def init_travel_system(db_path=None):
    conn=_connect(db_path)
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS location_travels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
            from_node TEXT NOT NULL,to_node TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','arrived','cancelled','failed')),
            revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>=1),
            started_at TEXT NOT NULL,arrival_at TEXT NOT NULL,cancelled_at TEXT,completed_at TEXT,
            created_at TEXT NOT NULL,updated_at TEXT NOT NULL,CHECK(from_node<>to_node),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);
        CREATE UNIQUE INDEX IF NOT EXISTS ux_location_travels_one_active_user ON location_travels(user_id) WHERE status='active';
        CREATE INDEX IF NOT EXISTS ix_location_travels_due ON location_travels(status,arrival_at,id);
        CREATE INDEX IF NOT EXISTS ix_location_travels_user_history ON location_travels(user_id,id DESC);
        """); conn.commit(); return {'success':True,'table':'location_travels'}
    finally: conn.close()

def get_active_travel(user_id, *, db_path=None):
    conn=_connect(db_path)
    try: return _row(conn.execute("SELECT * FROM location_travels WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1",(int(user_id),)).fetchone())
    finally: conn.close()

def get_travel(travel_id, *, db_path=None):
    conn=_connect(db_path)
    try: return _row(conn.execute('SELECT * FROM location_travels WHERE id=?',(int(travel_id),)).fetchone())
    finally: conn.close()

def get_due_active_travels(*, now=None, limit=100, db_path=None):
    conn=_connect(db_path)
    try: return [dict(r) for r in conn.execute("SELECT * FROM location_travels WHERE status='active' AND arrival_at<=? ORDER BY arrival_at,id LIMIT ?",(_iso(now),max(1,int(limit)))).fetchall()]
    finally: conn.close()

def _availability(conn,user_id,to_node):
    user=conn.execute('SELECT current_location,level FROM users WHERE user_id=?',(int(user_id),)).fetchone()
    if not user: return {'success':False,'reason':'user_not_found'}
    source=str(user['current_location'] or CITY_NODE)
    target=str(to_node)
    if source not in WORLD_NODES: return {'success':False,'reason':'invalid_current_node','current_node':source}
    if target not in WORLD_NODES: return {'success':False,'reason':'unknown_destination'}
    if not are_adjacent(source,target): return {'success':False,'reason':'not_adjacent','from_node':source,'to_node':target}
    if target != CITY_NODE and not is_location_unlocked(target,int(user['level'] or 1)):
        return {'success':False,'reason':'location_locked','from_node':source,'to_node':target}
    return {'success':True,'from_node':source,'to_node':target,'level':int(user['level'] or 1)}

def start_travel(user_id,to_node,*,now=None,busy_checker=None,db_path=None):
    if busy_checker is not None:
        busy=busy_checker(int(user_id))
        if busy: return {'success':False,'reason':'player_busy','busy':busy if isinstance(busy,dict) else None}
    current=_utc(now); stamp=_iso(current); arrival=_iso(current+timedelta(seconds=TRAVEL_SECONDS))
    conn=_connect(db_path)
    try:
        conn.execute('BEGIN IMMEDIATE')
        available=_availability(conn,user_id,to_node)
        if not available['success']: conn.rollback(); return available
        active=conn.execute("SELECT * FROM location_travels WHERE user_id=? AND status='active'",(int(user_id),)).fetchone()
        if active: conn.rollback(); return {'success':False,'reason':'already_travelling','travel':dict(active)}
        cur=conn.execute("INSERT INTO location_travels(user_id,from_node,to_node,status,revision,started_at,arrival_at,created_at,updated_at) VALUES (?,?,?,'active',1,?,?,?,?)",
            (int(user_id),available['from_node'],available['to_node'],stamp,arrival,stamp,stamp))
        travel_id=int(cur.lastrowid); conn.commit()
        return {'success':True,'travel_id':travel_id,'from_node':available['from_node'],'to_node':available['to_node'],'started_at':stamp,'arrival_at':arrival,'travel_seconds':TRAVEL_SECONDS,'revision':1}
    except sqlite3.IntegrityError:
        conn.rollback(); return {'success':False,'reason':'already_travelling'}
    except Exception: conn.rollback(); raise
    finally: conn.close()

def cancel_travel(user_id,travel_id,*,expected_revision=None,now=None,db_path=None):
    stamp=_iso(now); conn=_connect(db_path)
    try:
        conn.execute('BEGIN IMMEDIATE')
        params=[stamp,stamp,int(travel_id),int(user_id)]; where="id=? AND user_id=? AND status='active' AND arrival_at>?"; params.append(stamp)
        if expected_revision is not None: where+=' AND revision=?'; params.append(int(expected_revision))
        cur=conn.execute(f"UPDATE location_travels SET status='cancelled',revision=revision+1,cancelled_at=?,updated_at=? WHERE {where}",params)
        if cur.rowcount==1: conn.commit(); return {'success':True,'status':'cancelled','travel_id':int(travel_id)}
        row=conn.execute('SELECT * FROM location_travels WHERE id=? AND user_id=?',(int(travel_id),int(user_id))).fetchone(); conn.rollback()
        return {'success':False,'reason':'not_cancellable','travel':_row(row)}
    except Exception: conn.rollback(); raise
    finally: conn.close()

def complete_travel(travel_id,*,now=None,db_path=None):
    stamp=_iso(now); conn=_connect(db_path)
    try:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT * FROM location_travels WHERE id=?',(int(travel_id),)).fetchone()
        if not row: conn.rollback(); return {'success':False,'reason':'travel_not_found'}
        if row['status']!='active': conn.rollback(); return {'success':False,'reason':'already_terminal','travel':dict(row)}
        if row['arrival_at']>stamp: conn.rollback(); return {'success':False,'reason':'not_due','travel':dict(row)}
        user=conn.execute('SELECT current_location FROM users WHERE user_id=?',(int(row['user_id']),)).fetchone()
        if not user or str(user['current_location'] or CITY_NODE)!=str(row['from_node']):
            conn.execute("UPDATE location_travels SET status='failed',revision=revision+1,completed_at=?,updated_at=? WHERE id=? AND status='active'",(stamp,stamp,int(travel_id))); conn.commit()
            return {'success':False,'reason':'source_changed','status':'failed'}
        cur=conn.execute("UPDATE location_travels SET status='arrived',revision=revision+1,completed_at=?,updated_at=? WHERE id=? AND status='active'",(stamp,stamp,int(travel_id)))
        if cur.rowcount!=1: conn.rollback(); return {'success':False,'reason':'terminal_claim_lost'}
        updated=conn.execute('UPDATE users SET current_location=? WHERE user_id=? AND current_location=?',(str(row['to_node']),int(row['user_id']),str(row['from_node'])))
        if updated.rowcount!=1: raise RuntimeError('atomic location update failed')
        conn.commit(); return {'success':True,'status':'arrived','travel_id':int(travel_id),'user_id':int(row['user_id']),'from_node':row['from_node'],'to_node':row['to_node']}
    except Exception: conn.rollback(); raise
    finally: conn.close()

def recover_due_travels(*,now=None,limit=100,db_path=None):
    results=[]
    for travel in get_due_active_travels(now=now,limit=limit,db_path=db_path): results.append(complete_travel(travel['id'],now=now,db_path=db_path))
    return {'success':True,'processed':len(results),'results':results}


# ROM 18.22.2 arrival notification worker
import threading
import time
_TRAVEL_WORKER_STARTED=False

def _arrival_keyboard(node_id):
    from keyboards import city_kb, main_kb
    return city_kb() if str(node_id)==CITY_NODE else main_kb()

def _send_arrival(bot,result):
    try:
        from handlers.map import build_map_inline_kb
        text=f"✅ Подорож завершено\n\nТи прибув у:\n{WORLD_NODES[result['to_node']]['name']}"
        bot.send_message(int(result['user_id']),text,reply_markup=_arrival_keyboard(result['to_node']))
        bot.send_message(int(result['user_id']),"🗺️ Доступні напрямки:",reply_markup=build_map_inline_kb(int(result['user_id'])))
        return True
    except Exception:
        return False

def recover_travels_after_restart(bot=None,now=None):
    recovered=recover_due_travels(now=now)
    notified=[]
    if bot is not None:
        for result in recovered['results']:
            if result.get('success') and _send_arrival(bot,result): notified.append(result['travel_id'])
    return {'success':True,'processed':recovered['processed'],'notified_travel_ids':notified,'results':recovered['results']}

def start_travel_worker(bot,interval_seconds=1.0):
    global _TRAVEL_WORKER_STARTED
    if _TRAVEL_WORKER_STARTED:return False
    _TRAVEL_WORKER_STARTED=True
    def worker():
        while True:
            try: recover_travels_after_restart(bot)
            except Exception: pass
            time.sleep(max(0.5,float(interval_seconds)))
    threading.Thread(target=worker,name='location-travel-worker',daemon=True).start();return True
