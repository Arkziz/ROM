from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
path=ROOT/'handlers/player_interaction.py';source=path.read_text(encoding='utf-8-sig');tree=ast.parse(source)
functions={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
for name in ('_send_trade_editor','_remember_player_trade_panel_18_22_6','_terminalize_player_trade_panel_18_22_6'):assert name in functions
send_source=ast.get_source_segment(source,functions['_send_trade_editor']) or ''
assert send_source.count('_remember_player_trade_panel_18_22_6(')==2
assert 'sent = bot.send_message(' in send_source and 'sent_id = getattr(sent, "message_id", None)' in send_source
sent_position = send_source.index('sent = bot.send_message(')
sent_id_position = send_source.index('sent_id = getattr(sent, "message_id", None)')
remember_positions = []
start = 0
while True:
 try:
  position = send_source.index('_remember_player_trade_panel_18_22_6(', start)
 except ValueError:
  break
 remember_positions.append(position)
 start = position + 1
assert len(remember_positions) == 2
assert sent_position < sent_id_position < remember_positions[-1]

class Msg:
 def __init__(self,mid):self.message_id=mid
class Bot:
 def __init__(self):self.sent=[];self.edited=[]
 def send_message(self,chat_id,text,**kwargs):self.sent.append((chat_id,text,kwargs));return Msg(777)
namespace={
 '_trade_editor_text':lambda state:'panel',
 '_trade_editor_kb':lambda trade_id,state=None:'keyboard',
 'get_player_trade_editor_state':lambda trade_id,user_id:{'success':True},
 '_safe_edit_message_text':lambda *a,**k:None,
}
refs=[];namespace['_remember_player_trade_panel_18_22_6']=lambda *a:refs.append(a)
exec(compile(ast.Module([functions['_send_trade_editor']],[]),str(path),'exec'),namespace)
bot=Bot();namespace['_send_trade_editor'](bot,202,202,7)
assert refs==[(7,202,202,777)],refs
assert bot.sent[0][2]['reply_markup']=='keyboard'
refs.clear();namespace['_send_trade_editor'](bot,202,202,7,888)
assert refs==[(7,202,202,888)],refs
print('{"status":"PASS","initial_recipient_panel_id":777,"edited_panel_id":888,"registry_updates":2}')
