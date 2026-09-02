#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main():
 src=(ROOT/'handlers'/'crystal_shop.py').read_text(encoding='utf-8-sig');tree=ast.parse(src)
 cb=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='callback'];assert len(cb)==1
 block=ast.get_source_segment(src,cb[0]) or ''
 assert "if action in ('buy','execute'):" in block
 assert block.count('purchase_crystal_shop_item(uid,iid,qty,key)')==1
 assert '⚠️ Остаточне підтвердження' not in block and '✅ Так, купити' not in block and 'cs:execute:' not in block
 assert '✅ Підтвердити покупку' in block and 'cs:buy:' in block
 module_block=src
 assert 'EXP_BONUS_BUTTON' in module_block and 'k.add(EXP_BONUS_BUTTON)' in module_block
 assert 'BAG_EXPANSION_BUTTON' in module_block and 'def bag_expansion_callback(call):' in module_block
 assert "startswith('bg:')" in module_block and 'purchase_crystal_bag_expansion' in module_block
 print('PASS: single confirmation, compatibility route, bonus and bag entry points preserved')
if __name__=='__main__':main()
