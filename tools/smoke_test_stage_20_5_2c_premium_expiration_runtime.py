#!/usr/bin/env python3
from __future__ import annotations
import ast
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def getfn(text):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_format_premium_expiration_kyiv'];assert len(nodes)==1;return ast.get_source_segment(text,nodes[0])
def main():
 files=[R/'handlers/timed_exp_bonus.py',R/'handlers/city.py']
 functions=[]
 for p in files:
  text=p.read_text(encoding='utf-8-sig');ast.parse(text);src=getfn(text);ns={};exec(src,ns);functions.append(ns['_format_premium_expiration_kyiv'])
 values=['2026-10-27T18:17:00+00:00','2026-10-27T18:17:00Z',datetime(2026,10,27,18,17,tzinfo=timezone.utc),datetime(2026,10,27,18,17)]
 for fn in functions:
  for value in values:assert fn(value)=='27.10.2026 20:17 за Києвом',(value,fn(value))
  assert fn(None)=='час завершення невідомий'
 print('[OK] Premium Kyiv formatter handles ISO, Z, aware datetime and naive datetime in both handlers')
if __name__=='__main__':main()
