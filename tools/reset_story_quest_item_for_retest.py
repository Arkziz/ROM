#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reset one exact retained story item for a controlled manual retest."""
from __future__ import annotations
import argparse,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
QUEST_ID='start_path_004_guard_uniform_scrap';ITEM_KEY='start_path_guard_uniform_scrap'
def parse_args():
 p=argparse.ArgumentParser();p.add_argument('--character',required=True);p.add_argument('--apply',action='store_true');return p.parse_args()
def main():
 args=parse_args();db_path=ROOT/'game.db';connection=sqlite3.connect(db_path);connection.row_factory=sqlite3.Row
 backup_dir=ROOT/'backup'/'stage_19_23_3h_story_quest_item_retest';report_dir=ROOT/'reports';backup_dir.mkdir(parents=True,exist_ok=True);report_dir.mkdir(parents=True,exist_ok=True)
 try:
  users=connection.execute('SELECT user_id,character_name FROM users WHERE character_name=?',(args.character,)).fetchall()
  if len(users)!=1:raise RuntimeError(f'expected one character, found {len(users)}')
  user_id=int(users[0]['user_id']);quest=connection.execute('SELECT * FROM user_story_quests WHERE user_id=? AND quest_id=?',(user_id,QUEST_ID)).fetchone();item=connection.execute('SELECT * FROM user_story_quest_items WHERE user_id=? AND quest_id=? AND item_key=?',(user_id,QUEST_ID,ITEM_KEY)).fetchone()
  if quest is None or quest['status']!='ACTIVE':raise RuntimeError('quest 4 must be ACTIVE')
  if item is None or int(item['quantity'])<=0:raise RuntimeError('quest item quantity is already zero or missing')
  evidence={'character':args.character,'user_id':user_id,'quest_before':dict(quest),'item_before':dict(item),'apply':bool(args.apply),'generated_at_utc':datetime.now(timezone.utc).isoformat(),'wal_shm_manipulated':False}
  stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup_path=backup_dir/f'quest_4_item_{user_id}_{stamp}.json';backup_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
  if not args.apply:
   print(json.dumps({'status':'DRY_RUN','backup':str(backup_path.relative_to(ROOT)),'quantity':int(item['quantity'])},ensure_ascii=False,indent=2));return 0
  connection.execute('BEGIN IMMEDIATE')
  updated=connection.execute('UPDATE user_story_quest_items SET quantity=0,updated_at=? WHERE user_id=? AND quest_id=? AND item_key=? AND quantity=?',(datetime.now(timezone.utc).isoformat(),user_id,QUEST_ID,ITEM_KEY,int(item['quantity'])))
  if updated.rowcount!=1:raise RuntimeError('exact item row changed concurrently')
  after=connection.execute('SELECT * FROM user_story_quest_items WHERE user_id=? AND quest_id=? AND item_key=?',(user_id,QUEST_ID,ITEM_KEY)).fetchone();quest_after=connection.execute('SELECT * FROM user_story_quests WHERE user_id=? AND quest_id=?',(user_id,QUEST_ID)).fetchone()
  if after is None or int(after['quantity'])!=0 or quest_after['status']!='ACTIVE':raise RuntimeError('postcondition failed')
  connection.commit();report={'status':'PASS','character':args.character,'user_id':user_id,'quest_id':QUEST_ID,'item_key':ITEM_KEY,'quantity_before':int(item['quantity']),'quantity_after':0,'quest_status':'ACTIVE','backup':str(backup_path.relative_to(ROOT)),'wal_shm_manipulated':False};(report_dir/'stage_19_23_3h_story_quest_item_retest_reset.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));return 0
 except Exception:
  if connection.in_transaction:connection.rollback()
  raise
 finally:connection.close()
if __name__=='__main__':raise SystemExit(main())
