#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main():
 path=ROOT/'handlers'/'combat.py';src=path.read_text(encoding='utf-8-sig');tree=ast.parse(src)
 assert '(зброя:' not in src
 assignments=[node for node in ast.walk(tree) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='weapon_damage' for target in node.targets)]
 assert len(assignments)>=3, len(assignments)
 assert any(isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='get' and any(isinstance(arg,ast.Constant) and arg.value=='weapon_damage' for arg in node.value.args) for node in assignments)
 assert 'dmg' in src and 'enemy_action_text' in src
 assert any(isinstance(n,ast.FunctionDef) and n.name=='register_combat_handlers' for n in ast.walk(tree))
 print('PASS: technical weapon number removed; combat calculation inputs retained')
if __name__=='__main__':main()
