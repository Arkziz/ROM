from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/quest_item_store.py",ROOT/"rom_v2/application/quest_item_store_service.py"]
for path in files:
 text=path.read_text(encoding="utf-8")
 forbidden=("inventory_repository","inventory_service","equipment_repository","bag_capacity","inventory_id")
 hits=[x for x in forbidden if x in text]
 if hits:print(f"No regular inventory leakage: FAIL {path.name}:{hits}");sys.exit(1)
 ast.parse(text)
print("Stage 21.13.2c No regular inventory leakage: PASS")
