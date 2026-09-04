# -*- coding: utf-8 -*-
"""Persistent one-attempt-per-cycle inactivity reminder policy."""
from __future__ import annotations
import sqlite3
from datetime import datetime,timezone,timedelta
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/"game.db"
INACTIVITY_THRESHOLD_SECONDS=7*24*60*60
INACTIVITY_SCAN_INTERVAL_SECONDS=60*60
INACTIVITY_REMINDER_TEXT="💠 Руни знову кличуть вас!\n\nМинуло понад 7 днів від вашої останньої пригоди.\n\nСвіт продовжує змінюватися, а небезпечні землі все ще приховують здобич, руни та випробування.\n\nНатисніть /start, щоб повернутися до гри й продовжити свій шлях!"
def _utc(value=None):
 value=value or datetime.now(timezone.utc)
 if value.tzinfo is None:value=value.replace(tzinfo=timezone.utc)
 return value.astimezone(timezone.utc)
def _stamp(value=None):return _utc(value).isoformat()
def _connection(db_path=None):
 c=sqlite3.connect(str(db_path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute("PRAGMA busy_timeout=30000");return c
def init_inactivity_reminder_system(db_path=None):
 c=_connection(db_path)
 try:
  c.executescript("""CREATE TABLE IF NOT EXISTS inactivity_reminders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,inactivity_started_at TEXT NOT NULL,eligible_at TEXT NOT NULL,attempted_at TEXT NOT NULL,delivery_status TEXT NOT NULL CHECK(delivery_status IN ('pending','sent','blocked','failed')),error_type TEXT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(user_id,inactivity_started_at),FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);CREATE INDEX IF NOT EXISTS idx_inactivity_reminders_user ON inactivity_reminders(user_id,id DESC);CREATE INDEX IF NOT EXISTS idx_inactivity_reminders_status ON inactivity_reminders(delivery_status,attempted_at);""");c.commit();return {'success':True}
 finally:c.close()
def get_eligible_inactivity_users(now=None,db_path=None):
 current=_utc(now);cutoff=_stamp(current-timedelta(seconds=INACTIVITY_THRESHOLD_SECONDS));c=_connection(db_path)
 try:
  rows=c.execute("""SELECT u.user_id,u.last_activity_at,u.character_name,u.character_class FROM users u WHERE u.last_activity_at IS NOT NULL AND TRIM(COALESCE(u.character_name,''))<>'' AND TRIM(COALESCE(u.character_class,''))<>'' AND u.last_activity_at<=? AND NOT EXISTS(SELECT 1 FROM inactivity_reminders r WHERE r.user_id=u.user_id AND r.inactivity_started_at=u.last_activity_at) ORDER BY u.user_id""",(cutoff,)).fetchall();return [dict(r) for r in rows]
 finally:c.close()
def claim_inactivity_reminder(user_id,inactivity_started_at,now=None,db_path=None):
 current=_utc(now);started=str(inactivity_started_at or '').strip()
 if not started:return {'success':False,'claimed':False,'reason':'missing_cycle'}
 try:eligible=_stamp(datetime.fromisoformat(started.replace('Z','+00:00'))+timedelta(seconds=INACTIVITY_THRESHOLD_SECONDS))
 except Exception:return {'success':False,'claimed':False,'reason':'invalid_cycle'}
 c=_connection(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');row=c.execute("SELECT last_activity_at,character_name,character_class FROM users WHERE user_id=?",(int(user_id),)).fetchone()
  if not row or str(row['last_activity_at'] or '')!=started or not str(row['character_name'] or '').strip() or not str(row['character_class'] or '').strip():c.rollback();return {'success':False,'claimed':False,'reason':'stale_or_ineligible'}
  if current<datetime.fromisoformat(eligible):c.rollback();return {'success':False,'claimed':False,'reason':'not_due'}
  stamp=_stamp(current);cur=c.execute("INSERT OR IGNORE INTO inactivity_reminders(user_id,inactivity_started_at,eligible_at,attempted_at,delivery_status,error_type,created_at,updated_at) VALUES(?,?,?,?, 'pending',NULL,?,?)",(int(user_id),started,eligible,stamp,stamp,stamp));claimed=cur.rowcount==1;c.commit();return {'success':True,'claimed':claimed,'reason':'claimed' if claimed else 'already_attempted'}
 except Exception:c.rollback();raise
 finally:c.close()
def finalize_inactivity_reminder(user_id,inactivity_started_at,status,error_type=None,now=None,db_path=None):
 if status not in {'sent','blocked','failed'}:raise ValueError('invalid delivery status')
 c=_connection(db_path)
 try:
  cur=c.execute("UPDATE inactivity_reminders SET delivery_status=?,error_type=?,updated_at=? WHERE user_id=? AND inactivity_started_at=? AND delivery_status='pending'",(status,str(error_type or '')[:120] or None,_stamp(now),int(user_id),str(inactivity_started_at)));c.commit();return {'success':cur.rowcount==1,'updated':cur.rowcount}
 finally:c.close()
def classify_delivery_error(error):
 text=str(error or '').casefold();name=type(error).__name__
 return ('blocked',name) if any(x in text for x in ('blocked','bot was blocked','chat not found','user is deactivated')) else ('failed',name)
def process_inactivity_reminders(bot,now=None,db_path=None):
 current=_utc(now);result={'eligible':0,'claimed':0,'sent':0,'blocked':0,'failed':0}
 for row in get_eligible_inactivity_users(current,db_path):
  result['eligible']+=1;claim=claim_inactivity_reminder(row['user_id'],row['last_activity_at'],current,db_path)
  if not claim.get('claimed'):continue
  result['claimed']+=1
  try:bot.send_message(int(row['user_id']),INACTIVITY_REMINDER_TEXT);status,error_type='sent',None
  except Exception as error:status,error_type=classify_delivery_error(error)
  finalize_inactivity_reminder(row['user_id'],row['last_activity_at'],status,error_type,current,db_path);result[status]+=1
 return result
