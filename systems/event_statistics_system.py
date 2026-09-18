# -*- coding: utf-8 -*-
"""Canonical storage API for exactly-once event-mob victories."""
from datetime import datetime, timezone

def _text(value,name):
    result=str(value or "").strip()
    if not result: raise ValueError(f"{name} must be non-empty")
    return result

def record_event_mob_victory(conn,event_key,user_id,mob_key,terminal_event_id,*,now=None):
    event_key=_text(event_key,"event_key"); mob_key=_text(mob_key,"mob_key"); terminal_event_id=_text(terminal_event_id,"terminal_event_id"); user_id=int(user_id)
    timestamp=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    conn.execute("SAVEPOINT event_kill_record")
    try:
        cur=conn.execute("INSERT OR IGNORE INTO event_kill_receipts(event_key,terminal_event_id,user_id,mob_key,recorded_at) VALUES(?,?,?,?,?)",(event_key,terminal_event_id,user_id,mob_key,timestamp))
        if cur.rowcount==0:
            conn.execute("RELEASE event_kill_record"); return {"success":True,"recorded":False,"duplicate":True}
        conn.execute("""INSERT INTO event_kill_statistics(event_key,user_id,mob_key,kills,first_reached_at,updated_at) VALUES(?,?,?,?,?,?)
          ON CONFLICT(event_key,user_id,mob_key) DO UPDATE SET kills=kills+1,updated_at=excluded.updated_at""",(event_key,user_id,mob_key,1,timestamp,timestamp))
        kills=conn.execute("SELECT kills FROM event_kill_statistics WHERE event_key=? AND user_id=? AND mob_key=?",(event_key,user_id,mob_key)).fetchone()[0]
        conn.execute("RELEASE event_kill_record"); return {"success":True,"recorded":True,"duplicate":False,"kills":int(kills)}
    except Exception:
        conn.execute("ROLLBACK TO event_kill_record"); conn.execute("RELEASE event_kill_record"); raise

def get_event_kill_leaderboard(conn,event_key,mob_key,*,page=1,page_size=10,top_size=100,user_id=None):
    event_key=_text(event_key,"event_key"); mob_key=_text(mob_key,"mob_key"); page=max(1,int(page)); page_size=int(page_size); top_size=int(top_size)
    if page_size!=10 or top_size!=100: raise ValueError("canonical leaderboard requires page_size=10 and top_size=100")
    rows=conn.execute("""SELECT user_id,kills,first_reached_at FROM event_kill_statistics WHERE event_key=? AND mob_key=?
      ORDER BY kills DESC,first_reached_at ASC,user_id ASC LIMIT ? OFFSET ?""",(event_key,mob_key,min(page_size,max(0,top_size-(page-1)*page_size)),(page-1)*page_size)).fetchall()
    own=None
    if user_id is not None:
        ranked=conn.execute("""SELECT user_id,kills,first_reached_at FROM event_kill_statistics WHERE event_key=? AND mob_key=? ORDER BY kills DESC,first_reached_at ASC,user_id ASC""",(event_key,mob_key)).fetchall()
        for index,row in enumerate(ranked,1):
            if int(row[0])==int(user_id): own={"rank":index,"user_id":int(row[0]),"kills":int(row[1])}; break
    return {"page":page,"page_size":10,"top_size":100,"entries":[{"rank":(page-1)*10+i,"user_id":int(r[0]),"kills":int(r[1])} for i,r in enumerate(rows,1)],"own":own}
