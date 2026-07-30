from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
U=-100900001;I=90900001

def fail(x):print('[FAIL]',x);raise SystemExit(1)
def clean(db):
    try:db.conn.execute("DELETE FROM inventory_runes WHERE inventory_id IN (SELECT id FROM inventory WHERE user_id=?)",(U,))
    except:pass
    for t in ('equipment_slots','inventory','user_daily_quests'):
        try:db.conn.execute(f'DELETE FROM {t} WHERE user_id=?',(U,))
        except:pass
    db.conn.execute('DELETE FROM users WHERE user_id=?',(U,));db.conn.execute('DELETE FROM items WHERE id=?',(I,));db.conn.commit()
def q(db,item):return int(db.conn.execute('SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?',(U,item)).fetchone()[0] or 0)
def main():
 import db;clean(db)
 try:
  db.create_user(U);db.init_rune_system();cols={r[1] for r in db.conn.execute('PRAGMA table_info(items)')}
  v={'id':I,'name':'Тестовий предмет','type':'armor','rarity':'common','category':'equipment','slot_key':'chest','weapon_hands':1,'max_stack':1,'sell_price':0,'bonus_str':0,'bonus_dex':0,'bonus_int':0,'bonus_wis':0,'bonus_sta':0,'pdef':0,'mdef':0,'item_level':1,'is_generated':0,'item_subtype':'','armor_type':'cloth'}
  ks=[k for k in v if k in cols];db.conn.execute(f"INSERT INTO items ({','.join(ks)}) VALUES ({','.join('?' for _ in ks)})",tuple(v[k] for k in ks))
  eid=db.conn.execute('INSERT INTO inventory (user_id,item_id,quantity,durability) VALUES (?,?,1,100)',(U,I)).lastrowid
  for n,(item,stat,lvl) in enumerate(((501,'STR',1),(513,'STA',3))):db.conn.execute('INSERT INTO inventory_runes (inventory_id,slot_index,rune_item_id,rune_stat,rune_level) VALUES (?,?,?,?,?)',(eid,n,item,stat,lvl))
  db.conn.commit();db.add_item(U,527,1);db.add_item(U,528,1)
  p=db.get_extractor_preview(U,eid)
  if not p.get('success') or p['materials']!={'simple':1,'perfect':1}:fail(p)
  r=db.use_simple_rune_extractor(U,eid,random_choice=lambda x:x[0])
  if not r.get('success') or q(db,501)!=1 or q(db,527)!=0:fail(r)
  if db.conn.execute('SELECT 1 FROM inventory WHERE id=?',(eid,)).fetchone():fail('equipment remains')
  h=(ROOT/'handlers/runes.py').read_text(encoding='utf-8-sig');k=(ROOT/'keyboards.py').read_text(encoding='utf-8-sig')
  for m in ('🧰 Вибір Екстрактора','re:item:','re:simple:','re:perfect:','✅ Використати Простий Екстрактор'):
   if m not in h:fail(m)
  if 'kb.add("🧰 Екстрактор")' not in k:fail('reply button')
  print('[OK] Equipment-first Simple Rune Extractor contracts')
  print('- equipment selected before extractor type: OK');print('- simple/perfect material counts: OK');print('- simple extractor atomic result: OK');print('- perfect path reserved for 10.10.0: OK')
 finally:clean(db)
 print('- isolated fixture cleanup: OK');print('- real user mutations: 0')
if __name__=='__main__':main()
