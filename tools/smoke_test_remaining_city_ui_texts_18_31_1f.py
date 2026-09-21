#!/usr/bin/env python3
import importlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
for name in ['handlers.city', 'handlers.runes']:importlib.import_module(name)
texts=[]
for rel in ['handlers/city.py', 'handlers/runes.py']:
 s=(ROOT/rel).read_text(encoding='utf-8');texts.append(s)
all_text=chr(10).join(texts)
for stale in ['⚒️ КОВАЛЬ: РЕМОНТ ТА КУЗНЯ', '📦 Стан твого спорядження:', '💳 Разом за повний ремонт:', 'Для майбутнього вилучення знадобиться Екстрактор рун.', 'Поки що таверна працює як атмосферне місце для майбутніх функцій.']:assert stale not in all_text,stale
for current in ['🛠️ Ремонт спорядження', '📦 Стан спорядження:', '💳 Вартість повного ремонту:', 'Для вилучення руни знадобиться Екстрактор рун.', 'Після вставлення руна закріплюється за предметом.', 'Поки що тут можна відпочити від подорожей і послухати розмови мандрівників.', 'Максимум у стаку:']:assert current in all_text,current
assert '💰 Твоє золото:' not in all_text
print('[PASS] remaining city UI texts normalized and modules import')
