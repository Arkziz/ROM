#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.telegram_rate_limit import is_expired_callback_query_error

def main():
 pve=(ROOT/'systems'/'pve_auto_escape_system.py').read_text(encoding='utf-8-sig');rate=(ROOT/'systems'/'telegram_rate_limit.py').read_text(encoding='utf-8-sig')
 assert 'from db_modules.connection import conn, cursor' not in pve and 'cursor.execute(' not in pve
 assert pve.count('conn.execute(')>=8 and 'with _LOCK:' in pve
 stale=Exception('A request to the Telegram API was unsuccessful. Error code: 400. Description: Bad Request: query is too old and response timeout expired or query ID is invalid')
 assert is_expired_callback_query_error('answer_callback_query',stale) is True
 assert is_expired_callback_query_error('send_message',stale) is False
 assert is_expired_callback_query_error('answer_callback_query',Exception('Error code: 400. Bad Request: chat not found')) is False
 assert is_expired_callback_query_error('answer_callback_query',Exception('Error code: 429. Too Many Requests')) is False
 assert 'Gameplay mutation was not replayed and polling may continue.' in rate
 # Exercise independent cursor creation on one cross-thread-enabled connection.
 import sqlite3
 c=sqlite3.connect(':memory:',check_same_thread=False);c.execute('CREATE TABLE t(v INTEGER)');errors=[]
 def worker(base):
  try:
   for value in range(base,base+100):c.execute('INSERT INTO t VALUES(?)',(value,))
  except Exception as error:errors.append(error)
 lock=threading.Lock()
 def serialized(base):
  with lock:worker(base)
 threads=[threading.Thread(target=serialized,args=(n*100,)) for n in range(2)]
 for t in threads:t.start()
 for t in threads:t.join()
 assert not errors and c.execute('SELECT COUNT(*) FROM t').fetchone()[0]==200;c.close()
 print('PVE CURSOR AND STALE CALLBACK CONTAINMENT: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
