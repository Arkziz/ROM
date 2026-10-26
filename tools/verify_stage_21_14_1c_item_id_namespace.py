from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/item_id_namespace.py",ROOT/"rom_v2/application/item_id_namespace_service.py"]
for p in files:
 s=p.read_text(encoding="utf-8");ast.parse(s)
 for forbidden in ("sqlite3","db_modules","handlers","aiogram"):
  assert forbidden not in s, (p,forbidden)
assert "preview_promotions.get(preview_id)" in files[1].read_text(encoding="utf-8")
print("Stage 21.14.1c item ID namespace boundary: PASS")
