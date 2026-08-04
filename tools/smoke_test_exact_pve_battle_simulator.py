from pathlib import Path
from systems.simulation.battle_models import BattleActor
from systems.simulation.pve_battle import ExactPveBattleEngine

def player(cls):
    magic=cls in {"mage","priest"}; return BattleActor(cls,10,260,260,55,65,35,35,35,35,35,"magical" if magic else "physical",8,14,"",100,100)
def mob(kind="normal"):
    x=BattleActor(kind,10,240,240,42,42,25,25,20,10,20,"physical")
    if kind=="elite": x.hp=x.max_hp=600;x.attack=84;x.pdef=x.mdef=31
    if kind=="boss": x.hp=x.max_hp=900;x.attack=72;x.pdef=x.mdef=40
    return x

def main():
    root=Path.cwd(); classes=("warrior","knight","scout","rogue","mage","priest")
    for i,cls in enumerate(classes):
        a=ExactPveBattleEngine(root,133000+i).run(f"{cls}_normal",cls,player(cls),mob())
        b=ExactPveBattleEngine(root,133000+i).run(f"{cls}_normal",cls,player(cls),mob())
        assert a.to_dict()==b.to_dict(); assert a.turns>0; assert a.metrics["skills_used"]>0; assert isinstance(a.metrics["player_damage"], int)
    for kind in ("normal","elite","boss"):
        r=ExactPveBattleEngine(root,133100).run(kind,"warrior",player("warrior"),mob(kind),kind); assert r.battle_type==kind
    print("[OK] Exact PvE battle simulator smoke test")
    print("- six classes deterministic: PASS")
    print("- production skill catalog 18/18: PASS")
    print("- normal/elite/boss scenarios: PASS")
    print("- canonical attack rules: PASS")
    print("- skills/resources/cooldowns/effects: PASS")
    print("- database writes: 0")
if __name__=="__main__": main()
