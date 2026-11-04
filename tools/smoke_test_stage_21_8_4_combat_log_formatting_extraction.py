from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("combat_formatting",root/"handlers"/"combat_formatting.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert callable(module.build_lethal_combat_log)
source=(root/"handlers"/"combat_formatting.py").read_text(encoding="utf-8-sig")
for token in ("ПРОМАХ","Навичка застосована","ОСТАННІЙ ХІД","Здоров’я противника"):
 assert token in source,token
print("PASS: Stage 21.8.4 isolated combat formatting import and branch markers")
