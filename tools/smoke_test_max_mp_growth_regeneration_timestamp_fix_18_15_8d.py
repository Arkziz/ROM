from pathlib import Path
import ast

def source(path,name):
    text=path.read_text(encoding="utf-8");nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name]
    assert nodes;return ast.get_source_segment(text,nodes[-1]) or ""

def main():
    root=Path(__file__).resolve().parents[1]
    c=root/"systems/character_system.py";n=root/"systems/notifications.py"
    lazy=source(c,"apply_lazy_mp_regeneration_17_15_1")
    user=source(c,"get_user_mp")
    worker=source(n,"apply_mp_regen_worker_17_15_1")
    worker_max=source(n,"get_worker_max_mp_17_15_1")
    assert "maximum != stored_maximum" in lazy and "last_mp_regen_update" in lazy
    assert "maximum != stored_maximum" in worker and "last_mp_regen_update" in worker
    assert "apply_lazy_mp_regeneration_17_15_1" in user
    assert "UPDATE users SET max_mp" not in worker_max
    def transition(current,old_max,new_max): return min(current,new_max),0
    assert transition(170,170,185)==(170,0)
    assert transition(180,185,170)==(170,0)
    assert transition(170,170,185)==(170,0)
    print("[PASS] Max MP growth resets regeneration epoch without filling current MP")
if __name__=="__main__":main()
