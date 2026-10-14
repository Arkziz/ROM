#!/usr/bin/env python3
"""Acceptance checks for the 3-token daily quest reward."""
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.balance import DAILY_QUEST_REWARD_ITEM_ID,DAILY_QUEST_REWARD_QUANTITY
from data.runes import FIRIUS_TOKEN_ITEM_ID,FIRIUS_TOKENS_PER_DAILY_REWARD,RUNE_FUSION_TOKEN_QUANTITY

def main():
 assert FIRIUS_TOKENS_PER_DAILY_REWARD==3
 assert FIRIUS_TOKEN_ITEM_ID==726
 assert RUNE_FUSION_TOKEN_QUANTITY==1
 assert DAILY_QUEST_REWARD_ITEM_ID==401
 assert DAILY_QUEST_REWARD_QUANTITY==3
 daily=(ROOT/'handlers/daily.py').read_text(encoding='utf-8-sig')
 system=(ROOT/'systems/rune_system.py').read_text(encoding='utf-8-sig')
 assert 'from data.runes import FIRIUS_TOKENS_PER_DAILY_REWARD' in daily
 daily_tree=ast.parse(daily)
 preview_nodes=[]
 for node in ast.walk(daily_tree):
  if not isinstance(node,ast.JoinedStr):continue
  constants=''.join(part.value for part in node.values if isinstance(part,ast.Constant) and isinstance(part.value,str))
  names=[part.value.id for part in node.values if isinstance(part,ast.FormattedValue) and isinstance(part.value,ast.Name)]
  if 'Жетон Фіріуса ×' in constants:preview_nodes.append((constants,names))
 assert len(preview_nodes)==1,preview_nodes
 # The daily text is one large f-string and legitimately also contains progress
 # variables. Require exactly one canonical token quantity reference without
 # constraining unrelated formatted values in the same preview block.
 preview_names=preview_nodes[0][1]
 assert preview_names.count('FIRIUS_TOKENS_PER_DAILY_REWARD')==1,preview_nodes
 assert 'Жетон Фіріуса ×5' not in daily
 assert system.count('FIRIUS_TOKENS_PER_DAILY_REWARD')>=3
 tree=ast.parse(system)
 fn=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='claim_daily_quest_reward_with_firius_tokens')
 body=''.join((ast.get_source_segment(system,fn) or '').lower().split())
 assert '_apply_stack_plan(conn,user_id,token_plan)' in body
 assert 'whereuser_id=?andcompleted=1andreward_claimed=0' in body
 assert 'deletefrominventory' not in body
 assert 'quantity=quantity-' not in body
 print('[OK] Daily reward - 3 Firius Tokens, 3 potions, canonical preview and exact-once credit')
 return 0
if __name__=='__main__':raise SystemExit(main())
