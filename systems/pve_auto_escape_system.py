#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persistent, atomic PvE encounter deadline and auto-escape owner."""
from __future__ import annotations
import json, threading, time, uuid
from datetime import datetime, timedelta, timezone
from db_modules.connection import conn, cursor
PVE_AUTO_ESCAPE_TIMEOUT_SECONDS = 300
PVE_AUTO_ESCAPE_SWEEP_SECONDS = 2
AUTO_ESCAPE_TEXT = "🏃 Бій завершено автоматично\n\nМинуло 5 хвилин із початку бою, тому персонаж утік.\n\nНагороди за цей бій не нараховано."
STALE_COMBAT_TEXT = "⚠️ Цей бій уже завершено."
_LOCK=threading.RLock(); _WORKER_STARTED=False

def _utcnow(): return datetime.now(timezone.utc)
def _iso(value): return value.astimezone(timezone.utc).isoformat()
def init_pve_auto_escape_system():
    with _LOCK:
        cursor.execute("""CREATE TABLE IF NOT EXISTS pve_encounters (
            encounter_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL UNIQUE,
            chat_id INTEGER NOT NULL, started_at TEXT NOT NULL, deadline_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active', terminal_reason TEXT DEFAULT '',
            terminal_at TEXT DEFAULT NULL, mob_snapshot_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            CHECK(status IN ('active','victory','defeat','manual_escape','auto_escape','replaced'))
        )""")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pve_encounters_status_deadline ON pve_encounters(status, deadline_at)")
        conn.commit()

def begin_pve_encounter(user_id, chat_id, mob, now=None, timeout_seconds=PVE_AUTO_ESCAPE_TIMEOUT_SECONDS):
    init_pve_auto_escape_system(); now=now or _utcnow(); deadline=now+timedelta(seconds=int(timeout_seconds)); eid=uuid.uuid4().hex
    payload=json.dumps(mob or {},ensure_ascii=False,default=str,separators=(',',':'))
    with _LOCK:
        try: conn.rollback()
        except Exception: pass
        conn.execute('BEGIN IMMEDIATE')
        cursor.execute("UPDATE pve_encounters SET status='replaced', terminal_reason='new_encounter', terminal_at=?, updated_at=? WHERE user_id=? AND status='active'",(_iso(now),_iso(now),int(user_id)))
        cursor.execute("""INSERT INTO pve_encounters(encounter_id,user_id,chat_id,started_at,deadline_at,status,mob_snapshot_json,created_at,updated_at)
        VALUES(?,?,?,?,?,'active',?,?,?)""",(eid,int(user_id),int(chat_id),_iso(now),_iso(deadline),payload,_iso(now),_iso(now)))
        conn.commit()
    return {'encounter_id':eid,'started_at':_iso(now),'deadline_at':_iso(deadline)}

def get_active_pve_encounter(user_id):
    init_pve_auto_escape_system(); row=cursor.execute("SELECT encounter_id,user_id,chat_id,started_at,deadline_at,mob_snapshot_json FROM pve_encounters WHERE user_id=? AND status='active'",(int(user_id),)).fetchone()
    if not row:return None
    return {'encounter_id':row[0],'user_id':row[1],'chat_id':row[2],'started_at':row[3],'deadline_at':row[4],'mob':json.loads(row[5] or '{}')}

def claim_pve_terminal(user_id, reason, encounter_id=None, now=None, require_expired=False):
    init_pve_auto_escape_system(); now=now or _utcnow(); allowed={'victory','defeat','manual_escape','auto_escape'}
    if reason not in allowed: raise ValueError('invalid PvE terminal reason')
    with _LOCK:
        try: conn.rollback()
        except Exception: pass
        conn.execute('BEGIN IMMEDIATE')
        sql="UPDATE pve_encounters SET status=?,terminal_reason=?,terminal_at=?,updated_at=? WHERE user_id=? AND status='active'"; args=[reason,reason,_iso(now),_iso(now),int(user_id)]
        if encounter_id: sql+=' AND encounter_id=?'; args.append(str(encounter_id))
        if require_expired: sql+=' AND deadline_at<=?'; args.append(_iso(now))
        changed=cursor.execute(sql,tuple(args)).rowcount==1
        conn.commit()
    return changed

def get_expired_active_pve_encounters(now=None, limit=100):
    init_pve_auto_escape_system(); now=now or _utcnow(); rows=cursor.execute("SELECT encounter_id,user_id,chat_id,deadline_at FROM pve_encounters WHERE status='active' AND deadline_at<=? ORDER BY deadline_at LIMIT ?",(_iso(now),int(limit))).fetchall()
    return [{'encounter_id':r[0],'user_id':r[1],'chat_id':r[2],'deadline_at':r[3]} for r in rows]

def expire_pve_encounters_once(bot, now=None):
    claimed=[]
    for row in get_expired_active_pve_encounters(now):
        if not claim_pve_terminal(row['user_id'],'auto_escape',row['encounter_id'],now,True): continue
        if hasattr(bot,'user_data'): bot.user_data.pop(row['user_id'],None)
        try: bot.send_message(row['chat_id'],AUTO_ESCAPE_TEXT)
        except Exception as error: print(f"PVE AUTO ESCAPE NOTICE FAILED user={row['user_id']}: {error}")
        claimed.append(row)
    return claimed

def recover_pve_encounters_after_restart(bot):
    """Runtime Telegram state cannot survive restart, so every persisted active encounter is terminally escaped using its original deadline semantics."""
    init_pve_auto_escape_system(); now=_utcnow(); rows=cursor.execute("SELECT encounter_id,user_id,chat_id FROM pve_encounters WHERE status='active'").fetchall(); claimed=[]
    for eid,uid,cid in rows:
        if claim_pve_terminal(uid,'auto_escape',eid,now,False):
            try: bot.send_message(cid,AUTO_ESCAPE_TEXT)
            except Exception as error: print(f"PVE RESTART ESCAPE NOTICE FAILED user={uid}: {error}")
            claimed.append(uid)
    return {'escaped_user_ids':claimed}

def start_pve_auto_escape_worker(bot):
    global _WORKER_STARTED
    init_pve_auto_escape_system()
    if _WORKER_STARTED:return False
    _WORKER_STARTED=True
    def loop():
        while True:
            try: expire_pve_encounters_once(bot)
            except Exception as error: print(f'PVE AUTO ESCAPE WORKER ERROR: {error}')
            time.sleep(PVE_AUTO_ESCAPE_SWEEP_SECONDS)
    threading.Thread(target=loop,name='pve-auto-escape',daemon=True).start(); return True
