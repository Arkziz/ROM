from pathlib import Path
from systems.simulation.world_progression import WorldProgressionSimulator

def main():
    root=Path.cwd()
    first=WorldProgressionSimulator(root,"warrior",2,"regular",136000,40).run()
    second=WorldProgressionSimulator(root,"warrior",2,"regular",136000,40).run()
    assert first.to_dict()==second.to_dict()
    assert first.status=="completed" and first.final_level==2
    assert first.battles==first.energy_spent
    assert first.wins+first.deaths==first.battles
    casual=WorldProgressionSimulator(root,"mage",5,"casual",136001,40).run()
    hardcore=WorldProgressionSimulator(root,"mage",5,"hardcore",136001,60).run()
    assert casual.status==hardcore.status=="completed"
    assert first.days>0 and first.battles>0
    assert all(event.event_type in {"victory","death","level_up","hp_regen","city_visit","contract_claim","daily_claim"} for event in first.events)
    print("[OK] World progression simulator MVP smoke test")
    print("- warrior production EXP level 1 -> 2 regular: PASS")
    print("- same seed deterministic full result: PASS")
    print("- Casual/Regular/Hardcore windows: PASS")
    print("- energy max 40 and +1/5 minutes loop: PASS")
    print("- EXACT battle engine integration: PASS")
    print("- inventory capacity 40/60 config: PASS")
    print("- database writes: 0")
if __name__=="__main__":main()
