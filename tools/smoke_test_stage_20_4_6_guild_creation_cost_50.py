#!/usr/bin/env python3
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def assignment(text,name):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
 assert len(nodes)==1,(name,len(nodes));return ast.literal_eval(nodes[0].value)
def function_source(text,name):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 assert len(nodes)==1,(name,len(nodes));return ast.get_source_segment(text,nodes[0]) or ''
def main():
 system=(ROOT/'systems/guild_system.py').read_text(encoding='utf-8-sig');handler=(ROOT/'handlers/guild.py').read_text(encoding='utf-8-sig')
 assert assignment(system,'GUILD_CREATE_COST_GOLD')==50.0
 assert assignment(system,'DEFAULT_GUILD_MEMBER_LIMIT')==10
 assert assignment(system,'MIN_GUILD_ACCESS_LEVEL')==3
 create=function_source(system,'create_guild');terms=function_source(system,'get_guild_creation_terms');confirm=function_source(handler,'build_guild_create_confirm_text')
 assert 'UPDATE users SET gold=ROUND(gold-?, 2) WHERE user_id=? AND gold>=?' in create
 assert '(GUILD_CREATE_COST_GOLD, user_id, GUILD_CREATE_COST_GOLD)' in create
 assert 'GUILD_CREATE_COST_GOLD:.2f' in create and 'guild_created' in create
 assert 'balance >= float(GUILD_CREATE_COST_GOLD)' in terms
 assert '"cost_gold": float(GUILD_CREATE_COST_GOLD)' in terms
 assert '{"cost_gold": 50.0, "gold_balance": 0.0, "member_limit": 10}' in confirm
 assert "terms['cost_gold']:.2f" in confirm
 assert 'GUILD_CREATE_COST_GOLD = 100.0' not in system
 print('[OK] Guild creation cost - canonical 50.00, atomic debit, terms/UI, level 3 and member limit 10')
if __name__=='__main__':main()
