#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast, sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from keyboards import rune_master_kb
from systems.name_rune_system import NAME_RUNE_DESCRIPTION, NAME_RUNE_ITEM_ID

def main():
 def text_of(button):
  if isinstance(button, dict):
   return str(button.get("text", ""))
  return str(getattr(button, "text", button))
 rows=[[text_of(button) for button in row] for row in rune_master_kb().keyboard]
 assert rows.count(["🧰 Екстрактор","🛒 Крамниця"])==1, rows
 assert NAME_RUNE_ITEM_ID==502 and NAME_RUNE_DESCRIPTION.strip()
 src=(ROOT/"handlers"/"inventory.py").read_text(encoding="utf-8-sig");ast.parse(src)
 assert src.count("from systems.name_rune_system import NAME_RUNE_DESCRIPTION")==1
 assert src.count("📖 Опис: {NAME_RUNE_DESCRIPTION}")==1
 print("PASS: Rune Master row and canonical Name Rune description")
if __name__=="__main__": main()
