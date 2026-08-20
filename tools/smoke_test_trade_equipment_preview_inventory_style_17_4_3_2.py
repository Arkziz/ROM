#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8')
tree=ast.parse(source)
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for name in ('_trade_preview_text_12_6_2','_trade_allowed_classes_text_17_4_3_2','_trade_snapshot_lines_12_6_2'):
 assert name in functions,name
preview=ast.get_source_segment(source,functions['_trade_preview_text_12_6_2'])
details=ast.get_source_segment(source,functions['_trade_snapshot_lines_12_6_2'])
assert '["📦 Предмет", "", f"<b>{name}</b>", ""]' in preview
for token in ('🧰 Тип: спорядження','🎯 Слот:','👤 Твій рівень:','🧱 Міцність:','📊 Бонуси:','format_equipment_rune_slots_text'):
 assert token in details,token
assert 'Зараз вдягнено для порівняння' not in details
assert 'Рідкість:' not in details
assert 'Тип броні:' not in details
assert source.count('ROM 17.4.3.2 ALIGN TRADE EQUIPMENT PREVIEW WITH INVENTORY')==1
print('[PASS] Stage 17.4.3.2 trade equipment preview inventory style')
