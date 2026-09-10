#!/usr/bin/env python3
import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/"handlers/inventory.py").read_text(encoding="utf-8-sig");ast.parse(source)
marker="# ROM Stage 18.16.10c unified sphere inventory cards."
assert source.count(marker)==1
segment=source[source.index(marker):]
for expected in ("🔮 Сфера нового шляху","♻️ Сфера Переродження","🧰 Категорія: Витратні предмети","📦 У цьому стакі: ×","🔄 Одноразовий предмет"):
 assert expected in segment,expected
assert "premium-предмет" not in segment
assert "Сфера не списується до остаточного підтвердження" in segment
assert "Сфера витрачається лише після успішної зміни класу" in segment
print("[PASS] Stage 18.16.10c unified sphere inventory card contract")
