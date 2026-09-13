from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
source=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
tree=ast.parse(source)
for name in ('_remember_player_trade_panel_18_22_6','_forget_player_trade_panel_18_22_6','_terminalize_player_trade_panel_18_22_6'):
 assert len([n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name])==1,name
assert source.count('_remember_player_trade_panel_18_22_6(')>=3
assert source.count('_terminalize_player_trade_panel_18_22_6(')>=3
assert 'reply_markup=None' in source
assert '❌ Обмін скасовано іншим гравцем.' in source

class Message:
 def __init__(self,chat_id,message_id):
  self.chat=type('Chat',(),{'id':chat_id})();self.message_id=message_id
class Bot:
 def __init__(self):self.edits=[];self.sent=[]
 def edit_message_text(self,text,chat_id,message_id,reply_markup=None):self.edits.append((text,chat_id,message_id,reply_markup))
 def edit_message_reply_markup(self,**kwargs):pass
 def send_message(self,*args,**kwargs):self.sent.append((args,kwargs));return Message(int(args[0]),900+len(self.sent))
namespace={}
required={'_PLAYER_TRADE_PANEL_REFS_18_22_6','_remember_player_trade_panel_18_22_6','_forget_player_trade_panel_18_22_6','_terminalize_player_trade_panel_18_22_6'}
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in required for t in node.targets):exec(compile(ast.Module([node],[]),str(ROOT/'handlers/player_interaction.py'),'exec'),namespace)
 if isinstance(node,ast.FunctionDef) and node.name in required:exec(compile(ast.Module([node],[]),str(ROOT/'handlers/player_interaction.py'),'exec'),namespace)
bot=Bot();remember=namespace['_remember_player_trade_panel_18_22_6'];terminal=namespace['_terminalize_player_trade_panel_18_22_6']
remember(7,101,101,501);remember(7,202,202,502)
a=terminal(bot,7,101,'own');b=terminal(bot,7,202,'other')
assert a['edited'] and b['edited']
assert bot.edits==[('own',101,501,None),('other',202,502,None)]
assert namespace['_PLAYER_TRADE_PANEL_REFS_18_22_6']=={}
print('{"status":"PASS","participants":2,"inline_keyboards_removed":2,"fallback_policy":"safe"}')
