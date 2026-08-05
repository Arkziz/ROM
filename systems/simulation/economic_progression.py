from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from .economic_ledger import EconomicResultCache,EconomicScenarioSpec,enrich_progression_result
from .world_progression import WorldProgressionSimulator

def run_economic_progression(root:Path,spec:EconomicScenarioSpec,force:bool=False):
    cache=EconomicResultCache(root)
    if not force:
        cached=cache.load(spec)
        if cached is not None:return cached
    sim=WorldProgressionSimulator(Path(root),spec.character_class,spec.target_level,spec.profile,spec.seed,inventory_capacity=spec.inventory_capacity,max_days=spec.max_days)
    result=sim.run(); payload=enrich_progression_result(result,sim.inventory,sim.equipment,asdict(spec)); cache.save(spec,payload); return payload
