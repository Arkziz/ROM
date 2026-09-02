#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
h=(ROOT/'handlers'/'admin_crystal_credit.py').read_text(encoding='utf-8-sig');s=(ROOT/'systems'/'admin_crystal_credit_system.py').read_text(encoding='utf-8-sig')
ast.parse(h);ast.parse(s)
assert 'account_menu_kb_17_30_1_4()' in h
assert "page_size=10" in h and "ac:history:" in h and "ac:history_close" in h
assert "ZoneInfo('Europe/Kyiv')" in h and '%d.%m.%Y %H:%M' in h
assert 'Операцій ще немає.' in h and 'Вилучено лише доступний залишок' in h
assert 'SELECT COUNT(*) FROM admin_crystal_credit_audit' in s and "'total_pages':total_pages" in s
assert 'DELETE FROM admin_crystal_credit_audit' not in s
print('PASS: canonical menu restore, permanent history, localized pagination')
