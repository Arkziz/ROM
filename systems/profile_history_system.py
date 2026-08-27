# -*- coding: utf-8 -*-
"""Stage 17.24 durable profile history readers and retention."""
import json, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/"game.db"
HISTORY_PAGE_SIZE=5
HISTORY_RETENTION_RECORDS_PER_USER=100
HISTORY_RETENTION_MIN_DAYS=60
PVP_REASON_UA={
 'afk_defeat':'поразка через бездіяльність',
 'opponent_afk':'перемога через бездіяльність суперника',
 'surrender':'власна здача' ,
 'opponent_surrender':'суперник здався',
 'hp_depleted':'завершення через втрату всіх ОЗ',
 'knockout':'перемога в бою',
 'max_rounds':'завершення після максимальної кількості раундів',
 'terminal':'бій завершено',
}
def localize_pvp_reason(reason, won=False):
 key=str(reason or '').strip().lower()
 if key=='surrender': return 'суперник здався' if won else 'власна здача'
 if key=='afk_defeat': return 'перемога через бездіяльність суперника' if won else 'поразка через бездіяльність'
 return PVP_REASON_UA.get(key,'бій завершено')

def _conn():
 c=sqlite3.connect(str(DB_PATH),timeout=30);c.row_factory=sqlite3.Row;return c
def _loads(value,fallback):
 try:return json.loads(value or '')
 except Exception:return fallback
def _name(c,uid):
 row=c.execute("SELECT COALESCE(character_name,'Гравець') FROM users WHERE user_id=?",(int(uid),)).fetchone();return str(row[0]) if row else 'Гравець'
def _fmt(value):
 if not value:return 'невідомо'
 try:
  dt=datetime.fromisoformat(str(value).replace('Z','+00:00'));return dt.astimezone().strftime('%d.%m.%Y %H:%M')
 except Exception:return str(value)
def init_profile_history():
 c=_conn()
 try:
  c.executescript("""CREATE INDEX IF NOT EXISTS ix_trade_history_completed_i ON player_trade_history(initiator_user_id,status,id DESC); CREATE INDEX IF NOT EXISTS ix_trade_history_completed_r ON player_trade_history(recipient_user_id,status,id DESC); CREATE INDEX IF NOT EXISTS ix_pvp_history_challenger ON pvp_battles(challenger_id,status,id DESC); CREATE INDEX IF NOT EXISTS ix_pvp_history_opponent ON pvp_battles(opponent_id,status,id DESC);""");c.commit()
 finally:c.close()
 return {'success':True}
def get_trade_history(user_id,page=0,page_size=HISTORY_PAGE_SIZE):
 uid=int(user_id);page=max(0,int(page));size=max(1,min(10,int(page_size)));c=_conn()
 try:
  total=c.execute("SELECT COUNT(*) FROM player_trade_history WHERE status='completed' AND (initiator_user_id=? OR recipient_user_id=?)",(uid,uid)).fetchone()[0]
  rows=c.execute("SELECT * FROM player_trade_history WHERE status='completed' AND (initiator_user_id=? OR recipient_user_id=?) ORDER BY COALESCE(completed_at,created_at) DESC,id DESC LIMIT ? OFFSET ?",(uid,uid,size,page*size)).fetchall();items=[]
  for row in rows:
   x=dict(row);other=int(x['recipient_user_id']) if uid==int(x['initiator_user_id']) else int(x['initiator_user_id']);own='initiator' if uid==int(x['initiator_user_id']) else 'recipient';give=_loads(x[own+'_offer_snapshot'],[]);take=_loads(x[('recipient' if own=='initiator' else 'initiator')+'_offer_snapshot'],[])
   items.append({'id':int(x['id']),'other_name':_name(c,other),'completed_at':_fmt(x.get('completed_at') or x.get('created_at')),'give':give,'take':take})
  return {'items':items,'page':page,'total':int(total),'has_prev':page>0,'has_next':(page+1)*size<int(total)}
 finally:c.close()
def _offer_lines(offers):
 lines=[]
 for o in offers or []:
  if o.get('asset_type')=='gold':lines.append(f"• {float(o.get('gold_amount') or 0):.2f} золота");continue
  snap=_loads(o.get('snapshot_json'),{}) if isinstance(o.get('snapshot_json'),str) else (o.get('snapshot') or {})
  name=str(snap.get('item_name') or snap.get('name') or 'Предмет');qty=int(o.get('quantity') or 1);ref=int(snap.get('refine_level') or 0);lines.append(f"• {name}{' +'+str(ref) if ref else ''} ×{qty}")
 return lines or ['• нічого']
def get_trade_history_detail(user_id,history_id):
 data=get_trade_history(user_id,0,100000)
 for x in data['items']:
  if x['id']==int(history_id):return {**x,'give_lines':_offer_lines(x['give']),'take_lines':_offer_lines(x['take'])}
 return None
def get_pvp_history(user_id,page=0,page_size=HISTORY_PAGE_SIZE):
 uid=int(user_id);page=max(0,int(page));size=max(1,min(10,int(page_size)));c=_conn()
 try:
  where="status='completed' AND winner_id IS NOT NULL AND (challenger_id=? OR opponent_id=?)"
  total=c.execute('SELECT COUNT(*) FROM pvp_battles WHERE '+where,(uid,uid)).fetchone()[0]
  rows=c.execute('SELECT * FROM pvp_battles WHERE '+where+' ORDER BY COALESCE(completed_at,created_at) DESC,id DESC LIMIT ? OFFSET ?',(uid,uid,size,page*size)).fetchall();items=[]
  for row in rows:
   x=dict(row);other=int(x['opponent_id']) if uid==int(x['challenger_id']) else int(x['challenger_id']);win=uid==int(x['winner_id'])
   items.append({'id':int(x['id']),'other_name':_name(c,other),'result':'Перемога' if win else 'Поразка','won':win,'rounds':int(x.get('round_number') or 1),'reason':localize_pvp_reason(x.get('result_reason'),win),'completed_at':_fmt(x.get('completed_at') or x.get('created_at'))})
  return {'items':items,'page':page,'total':int(total),'has_prev':page>0,'has_next':(page+1)*size<int(total)}
 finally:c.close()
def get_pvp_history_detail(user_id,battle_id):
 data=get_pvp_history(user_id,0,100000)
 return next((x for x in data['items'] if x['id']==int(battle_id)),None)
def cleanup_history_retention(preview=True,now=None):
 """Delete only shared records old >60d and outside last 100 for both users."""
 cutoff=(now or datetime.now(timezone.utc))-timedelta(days=HISTORY_RETENTION_MIN_DAYS);cut=cutoff.isoformat();c=_conn()
 try:
  trade=[r[0] for r in c.execute("""SELECT h.id FROM player_trade_history h WHERE h.status='completed' AND COALESCE(h.completed_at,h.created_at)<? AND h.id NOT IN (SELECT id FROM player_trade_history x WHERE x.status='completed' AND (x.initiator_user_id=h.initiator_user_id OR x.recipient_user_id=h.initiator_user_id) ORDER BY COALESCE(x.completed_at,x.created_at) DESC,x.id DESC LIMIT 100) AND h.id NOT IN (SELECT id FROM player_trade_history y WHERE y.status='completed' AND (y.initiator_user_id=h.recipient_user_id OR y.recipient_user_id=h.recipient_user_id) ORDER BY COALESCE(y.completed_at,y.created_at) DESC,y.id DESC LIMIT 100)""",(cut,))]
  pvp=[r[0] for r in c.execute("""SELECT b.id FROM pvp_battles b WHERE b.status='completed' AND b.winner_id IS NOT NULL AND COALESCE(b.completed_at,b.created_at)<? AND b.id NOT IN (SELECT id FROM pvp_battles x WHERE x.status='completed' AND x.winner_id IS NOT NULL AND (x.challenger_id=b.challenger_id OR x.opponent_id=b.challenger_id) ORDER BY COALESCE(x.completed_at,x.created_at) DESC,x.id DESC LIMIT 100) AND b.id NOT IN (SELECT id FROM pvp_battles y WHERE y.status='completed' AND y.winner_id IS NOT NULL AND (y.challenger_id=b.opponent_id OR y.opponent_id=b.opponent_id) ORDER BY COALESCE(y.completed_at,y.created_at) DESC,y.id DESC LIMIT 100)""",(cut,))]
  if not preview:
   c.executemany('DELETE FROM player_trade_history WHERE id=?',[(x,) for x in trade]);c.executemany('DELETE FROM pvp_battles WHERE id=?',[(x,) for x in pvp]);c.commit()
  return {'preview':bool(preview),'trade_ids':trade,'pvp_ids':pvp,'cutoff':cut}
 finally:c.close()
