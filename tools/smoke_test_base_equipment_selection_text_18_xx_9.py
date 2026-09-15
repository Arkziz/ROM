# -*- coding: utf-8 -*-
import ast
from pathlib import Path
source=Path("handlers/city.py").read_text(encoding="utf-8-sig")
tree=ast.parse(source)
owners=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="build_common_equipment_slot_choice_text"]
assert len(owners)==1
node=owners[0]
values=[n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
blob="\n".join(values)
assert "Обери тип базової зброї для свого стилю бою." in blob
assert "Обери предмет для другої руки відповідно до свого стилю бою." in blob
for marker in ("⚔️ Фізична зброя посилює фізичні атаки","🔮 Магічна зброя посилює магічні атаки","👐 Дворучна зброя займає обидві руки","🛡️ Щит підвищує фізичний захист і Витривалість","🔮 Магічний талісман підвищує магічний захист і Мудрість","🗡️ Зброя для другої руки підвищує атакувальні характеристики","ℹ️ Предмет для другої руки не можна використовувати разом із дворучною зброєю","Доступні варіанти:","buy_common_equipment:"):
    assert marker in blob, marker
for old in ("STR або DEX","INT/WIS","PDEF і STA","MDEF і WIS","не є танковим предметом"):
    assert old not in blob, old
calls={x.func.id if isinstance(x.func,ast.Name) else x.func.attr for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,(ast.Name,ast.Attribute))}
assert {"get_common_equipment_shop_suboffers","get_wallet","format_gold"} <= calls
print("BASE_EQUIPMENT_SELECTION_TEXT_18_XX_9_OK")
