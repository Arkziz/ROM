# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"handlers"/"event_ui.py").read_text(encoding="utf-8")
tree=ast.parse(source)
nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="_victory_count_text"]
assert len(nodes)==1
ns={}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"plural","exec"),ns)
f=ns["_victory_count_text"]
expected={0:"0 перемог",1:"1 перемога",2:"2 перемоги",3:"3 перемоги",4:"4 перемоги",5:"5 перемог",11:"11 перемог",12:"12 перемог",14:"14 перемог",21:"21 перемога",22:"22 перемоги",24:"24 перемоги",25:"25 перемог",101:"101 перемога",111:"111 перемог"}
for value,text in expected.items(): assert f(value)==text,(value,f(value))
rank=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="_rank_rows"]
assert len(rank)==1
rank_source=ast.get_source_segment(source,rank[0]) or ""
assert "g.tag" in rank_source
assert "g.name" not in rank_source
assert "_victory_count_text(row['kills'])" in rank_source
assert "Усього перемог:" in rank_source
assert "— {row['kills']} перемог" not in rank_source
print("EVENT_RANKING_PRESENTATION_18_29_4O_OK")
