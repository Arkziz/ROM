from systems.stat_system import calculate_max_mp

def main():
    assert calculate_max_mp("mage", level=1, intelligence=10, wisdom=10) == 170
    assert calculate_max_mp("priest", level=10, intelligence=30, wisdom=40) == 480
    assert calculate_max_mp("rogue", level=10, intelligence=999, wisdom=999) == 0
    base=calculate_max_mp("mage",level=10,intelligence=30,wisdom=30)
    assert calculate_max_mp("mage",level=10,intelligence=40,wisdom=30)-base == 20
    assert calculate_max_mp("mage",level=10,intelligence=30,wisdom=40)-base == 30
    assert calculate_max_mp("mage",level=11,intelligence=30,wisdom=30)-base == 20
    import ast
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    c=(root/"systems/character_system.py").read_text(encoding="utf-8")
    n=(root/"systems/notifications.py").read_text(encoding="utf-8")
    s=(root/"systems/simulation/combat_actor_stats.py").read_text(encoding="utf-8")
    ast.parse(c);ast.parse(n);ast.parse(s)
    active=[x for x in ast.parse(c).body if isinstance(x,ast.FunctionDef) and x.name=="get_max_mp"][-1]
    active_source=ast.get_source_segment(c,active) or ""
    assert "calculate_max_mp" in active_source and "get_player_stats" in active_source
    worker=[x for x in ast.parse(n).body if isinstance(x,ast.FunctionDef) and x.name=="get_worker_max_mp_17_15_1"][-1]
    worker_source=ast.get_source_segment(n,worker) or ""
    assert "calculate_max_mp" in worker_source and "get_worker_equipped_int_wis_totals_18_15_8c" in worker_source
    snapshot=[x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name=="build_combat_stat_snapshot"][-1]
    snapshot_source=ast.get_source_segment(s,snapshot) or ""
    assert "calculate_max_mp" in snapshot_source
    assert "stats[\"int\"]*3+stats[\"wis\"]*2" not in snapshot_source.replace(" ","")
    print("[PASS] foreground/worker/simulator Max MP production switch")
if __name__=="__main__":main()
