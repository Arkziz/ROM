from __future__ import annotations
import sqlite3, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import importlib.util
from systems.travel_system import start_travel,cancel_travel,complete_travel,get_active_travel,recover_due_travels

def main():
    now=datetime(2026,9,13,0,0,tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'test.db'; c=sqlite3.connect(db)
        c.execute('CREATE TABLE users(user_id INTEGER PRIMARY KEY,current_location TEXT,level INTEGER)')
        c.executemany('INSERT INTO users VALUES (?,?,?)',[(1,'city',1),(2,'start_path',1),(3,'start_path',6),(4,'dark_forest',10)])
        c.commit();c.close()
        spec=importlib.util.spec_from_file_location('m049',Path(__file__).resolve().parents[1]/'migrations/049_persistent_location_travel.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        c=sqlite3.connect(db); module.up(c); c.commit(); c.close()
        a=start_travel(1,'start_path',now=now,db_path=db); assert a['success'] and a['travel_seconds']==60
        assert not start_travel(1,'start_path',now=now,db_path=db)['success']
        assert not complete_travel(a['travel_id'],now=now+timedelta(seconds=59),db_path=db)['success']
        assert complete_travel(a['travel_id'],now=now+timedelta(seconds=60),db_path=db)['success']
        c=sqlite3.connect(db); assert c.execute('SELECT current_location FROM users WHERE user_id=1').fetchone()[0]=='start_path';c.close()
        locked=start_travel(2,'dark_forest',now=now,db_path=db); assert locked['reason']=='location_locked'
        b=start_travel(3,'dark_forest',now=now,db_path=db); assert b['success']
        assert cancel_travel(3,b['travel_id'],expected_revision=1,now=now+timedelta(seconds=10),db_path=db)['success']
        assert get_active_travel(3,db_path=db) is None
        assert not start_travel(4,'city',now=now,db_path=db)['success']
        c=start_travel(4,'start_path',now=now,db_path=db); assert c['success']
        rec=recover_due_travels(now=now+timedelta(seconds=70),db_path=db); assert rec['processed']==1 and rec['results'][0]['success']
        con=sqlite3.connect(db); assert con.execute('PRAGMA quick_check').fetchone()[0]=='ok'; assert not con.execute('PRAGMA foreign_key_check').fetchall(); con.close()
    print('{"status":"PASS","tests":9,"travel_seconds":60,"db":"temporary"}')
if __name__=='__main__': main()
