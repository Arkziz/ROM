#!/usr/bin/env python3
"""Structural acceptance for canonical Firius Token item description."""
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.runes import FIRIUS_TOKEN_ITEM_ID,FIRIUS_TOKENS_PER_DAILY_REWARD,RUNE_FUSION_TOKEN_QUANTITY

def main():
 assert FIRIUS_TOKEN_ITEM_ID==726
 assert FIRIUS_TOKENS_PER_DAILY_REWARD==3
 assert RUNE_FUSION_TOKEN_QUANTITY==1
 source=(ROOT/'handlers/inventory.py').read_text(encoding='utf-8-sig')
 assert 'from data.runes import FIRIUS_TOKENS_PER_DAILY_REWARD' in source
 assert '5 жетонів можна отримати за виконання щоденного завдання' not in source
 tree=ast.parse(source)
 fn=next(node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='get_refine_material_description_text')
 body=ast.get_source_segment(source,fn) or ''
 joined=[]
 for node in ast.walk(fn):
  if not isinstance(node,ast.JoinedStr):continue
  constants=''.join(part.value for part in node.values if isinstance(part,ast.Constant) and isinstance(part.value,str))
  names=[part.value.id for part in node.values if isinstance(part,ast.FormattedValue) and isinstance(part.value,ast.Name)]
  if 'жетон' in constants and 'щоденного завдання' in constants:joined.append((constants,names))
 assert len(joined)==1,joined
 assert joined[0][1].count('FIRIUS_TOKENS_PER_DAILY_REWARD')==1,joined
 assert 'одна успішна переробка витрачає 1 жетон' in body
 assert '3 однакові руни одного типу й рівня' in body
 print('[OK] Firius Token item description - canonical daily quantity 3 and unchanged fusion rules')
 return 0
if __name__=='__main__':raise SystemExit(main())
