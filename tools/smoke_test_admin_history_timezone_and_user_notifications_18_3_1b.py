#!/usr/bin/env python3
from pathlib import Path
import ast,os,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from handlers.admin_crystal_credit import _format_history_time,_notification_text,_notify_target
assert _format_history_time('2026-09-02T20:00:00+00:00')
assert _format_history_time('not-a-time')=='not-a-time'
credit={'operation':'credit','requested_amount':100,'actual_amount':100,'balance_before':40,'balance_after':140}
debit={'operation':'debit','requested_amount':100,'actual_amount':40,'balance_before':40,'balance_after':0}
assert 'Нараховано: 100' in _notification_text(credit,'test')
assert 'Запитано вилучити: 100' in _notification_text(debit,'test') and 'Фактично вилучено: 40' in _notification_text(debit,'test')
class Bot:
 def __init__(self,fail=False):self.sent=[];self.fail=fail
 def send_message(self,uid,text):
  if self.fail:raise RuntimeError('blocked')
  self.sent.append((uid,text))
b=Bot();r=_notify_target(b,1,credit,'test');assert r['delivered'] and len(b.sent)==1
r=_notify_target(b,1,dict(credit,idempotent_replay=True),'test');assert not r['attempted'] and len(b.sent)==1
r=_notify_target(Bot(True),1,debit,'test');assert r['attempted'] and not r['delivered']
print('PASS: timezone fallback, credit/debit notifications, replay and delivery failure')
