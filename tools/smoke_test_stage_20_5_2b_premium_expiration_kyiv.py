#!/usr/bin/env python3
from __future__ import annotations
import ast,sys,types
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def source(text,name):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 assert len(nodes)==1,(name,len(nodes));return ast.get_source_segment(text,nodes[0]) or ''
def main():
 premium=(ROOT/'handlers/timed_exp_bonus.py').read_text(encoding='utf-8-sig');city=(ROOT/'handlers/city.py').read_text(encoding='utf-8-sig')
 ast.parse(premium);ast.parse(city)
 assert premium.count('def _format_premium_expiration_kyiv(value):')==1
 assert city.count('def _format_premium_expiration_kyiv(value):')==1
 assert premium.count("_format_premium_expiration_kyiv(st['expires_at'])")==1
 assert premium.count("_format_premium_expiration_kyiv(p['expires_at_after'])")==1
 assert premium.count("_format_premium_expiration_kyiv(res['expires_at_after'])")==1
 assert city.count("_format_premium_expiration_kyiv(summary.get('expires_at'))")==2
 assert "_format_account_utc_17_30_1_1(summary.get('expires_at'))" not in city
 fn=source(premium,'_format_premium_expiration_kyiv');ns={'datetime':datetime,'timezone':timezone};exec(fn,ns)
 assert ns['_format_premium_expiration_kyiv']('2026-10-27T18:17:00+00:00')=='27.10.2026 20:17 за Києвом'
 assert ns['_format_premium_expiration_kyiv']('2026-12-27T18:17:00+00:00')=='27.12.2026 20:17 за Києвом'
 print('[OK] Premium expiration uses Europe/Kyiv and DD.MM.YYYY HH:MM за Києвом everywhere')
if __name__=='__main__':main()
