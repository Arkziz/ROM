#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.mana_skill_presentation import format_mana_cost_lines,format_mana_skill_presentation,strip_legacy_mana_cost_from_description

def main():
    fire={"cost_type":"mana","description":"Витрачає 20 MP та завдає 135% магічної шкоди.","mana_cost_flat":8,"mana_cost_max_mp_percent":7}
    assert format_mana_skill_presentation(fire,170)=="Завдає 135% магічної шкоди.\nВартість: 20 Мани\nФормула: 8 + 7% максимальної мани"
    assert format_mana_cost_lines(fire,300)=="Вартість: 29 Мани\nФормула: 8 + 7% максимальної мани"
    heal={"cost_type":"mana","description":"Витрачає 30 MP. Одразу лікує.","mana_cost_flat":12,"mana_cost_max_mp_percent":10}
    assert strip_legacy_mana_cost_from_description(heal)=="Одразу лікує."
    flow={"cost_type":"mana","description":"Не завдає шкоди.","mana_cost_flat":0,"mana_cost_max_mp_percent":0}
    assert format_mana_cost_lines(flow,170)=="Вартість: безкоштовно\nФормула: 0 + 0% максимальної мани"
    print("[OK] Dynamic Mana presentation contract")
    return 0
if __name__=="__main__": raise SystemExit(main())
