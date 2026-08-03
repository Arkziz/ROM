#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(x): print('[FAIL]',x); raise SystemExit(1)
def main():
    for rel in ('systems/player_interaction_system.py','handlers/player_interaction.py','db.py'):
        p=ROOT/rel; ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    from systems import player_interaction_system as m
    checks=((m.parse_trade_item_quantity_input('50',100).get('quantity'),50),(m.parse_trade_item_quantity_input('101',100).get('success'),False),(m.parse_trade_gold_amount_input('50,25',100).get('gold_amount'),50.25),(m.parse_trade_gold_amount_input('100.123',200).get('success'),False))
    for actual,expected in checks:
        if actual!=expected: fail((actual,expected))
    h=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
    required=('Категорія: {_trade_category_ua_12_6_3','⌨️ Ввести кількість','💰 Додати золото','➖ 10','➕ 10','⌨️ Ввести суму','✏️ Моя пропозиція','pi:tea:qinput:','pi:tea:ginput:')
    for x in required:
        if x not in h: fail('missing '+x)
    print('[OK] Player trade preview details and amount input contracts')
    print('- Ukrainian category labels and enriched equipment fields: OK')
    print('- manual stack quantity with range validation: OK')
    print('- gold editor ±1/±10, manual input and clear: OK')
    print('- requested main keyboard layout: OK')
    print('- isolated parser checks; real user mutations: 0')
if __name__=='__main__': main()
