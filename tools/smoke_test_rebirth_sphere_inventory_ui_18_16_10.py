#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/"handlers/inventory.py").read_text(encoding="utf-8-sig");tree=ast.parse(source)
assert "♻️ Сфера Переродження" in source
assert "🔮 Сфера нового шляху" in source
assert "📖 Опис:" in source
assert "rebirth:preview:" in source and "rebirth:final:" in source and "rebirth:confirm:" in source
assert "expected_item_id=504" in source
assert "Категорія: Витратні предмети" in source
print("[PASS] Stage 18.16.10 Rebirth Sphere inventory UI contract")
