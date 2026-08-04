from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import inspect
import json
import random
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .canonical_rules import RULES, call_rule, descriptor, rule_manifest
from .rng import SimulationRng


@dataclass
class ParityCase:
    case_id: str
    rule: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    seed: Optional[int] = None


@dataclass
class ParityResult:
    case_id: str
    rule: str
    passed: bool
    canonical: Any
    production: Any
    seed: Optional[int]
    error: str = ""


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except TypeError:
        return repr(value)


def _production_call(case: ParityCase) -> Any:
    item = descriptor(case.rule)
    module = __import__(item.module, fromlist=["*"])
    function = getattr(module, item.function)
    args = deepcopy(case.args)
    kwargs = deepcopy(case.kwargs)
    if not item.rng_injected:
        return function(*args, **kwargs)
    state = random.getstate()
    module_random = getattr(module, "random", None)
    try:
        random.seed(int(case.seed))
        if module_random is random:
            return function(*args, **kwargs)
        if module_random is None:
            raise RuntimeError(f"{item.module} has no random dependency")
        if hasattr(module_random, "seed"):
            module_random.seed(int(case.seed))
        return function(*args, **kwargs)
    finally:
        random.setstate(state)


def run_case(case: ParityCase) -> ParityResult:
    try:
        production = _production_call(case)
        rng = SimulationRng(int(case.seed)) if case.seed is not None else None
        canonical = call_rule(case.rule, *case.args, rng=rng, **case.kwargs)
        return ParityResult(
            case.case_id, case.rule, canonical == production,
            _jsonable(canonical), _jsonable(production), case.seed,
            "" if canonical == production else "result mismatch",
        )
    except Exception as error:
        return ParityResult(case.case_id, case.rule, False, None, None, case.seed, f"{type(error).__name__}: {error}")


def required_cases() -> List[ParityCase]:
    cases: List[ParityCase] = []
    for level in (1, 5, 10, 20):
        for value in (0, 1, 10, 50, 100, 250):
            cases.append(ParityCase(f"pcrit_{level}_{value}", "physical_crit_chance", (value, level), {}))
            cases.append(ParityCase(f"mcrit_{level}_{value}", "magical_crit_chance", (value, level), {}))
        for player_dex, mob_dex in ((0, 0), (10, 10), (25, 5), (5, 25), (100, 50)):
            cases.append(ParityCase(f"dodge_{level}_{player_dex}_{mob_dex}", "dodge_chance", (player_dex, mob_dex, level), {}))
    mob = {"name": "fixture", "hp": 100, "max_hp": 100, "attack": 20, "pdef": 12, "mdef": 8, "def": 10, "exp": 10, "gold": 5}
    cases.append(ParityCase("elite_modifier", "elite_modifier", (mob,), {}))
    for level, rarity, hands in ((1, "common", 1), (5, "uncommon", 1), (10, "rare", 2), (20, "epic", 2)):
        cases.append(ParityCase(f"weapon_{level}_{rarity}_{hands}", "weapon_damage", (level, rarity, hands), {}))
    for durability in (0, 1, 9, 10, 50, 99, 100):
        for rarity in ("common", "uncommon", "rare", "epic"):
            cases.append(ParityCase(f"repair_{durability}_{rarity}", "repair_cost", (durability, rarity), {}))
    for attack_type in ("physical", "magical"):
        cases.append(ParityCase(f"player_attack_{attack_type}", "player_attack", (50, 20, 30, 30, 10, attack_type, 5, 10), {}, 1302001))
        cases.append(ParityCase(f"mob_attack_{attack_type}", "mob_attack", (30, 20, 15, 25, 20, 20, 10, attack_type), {}, 1302002))
    return cases


def run_required_parity() -> Dict[str, Any]:
    results = [run_case(case) for case in required_cases()]
    passed = sum(1 for item in results if item.passed)
    payload = {
        "schema_version": "13.2.0",
        "verdict": "PASS" if passed == len(results) else "FAIL",
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "rule_manifest": rule_manifest(),
        "results": [asdict(item) for item in results],
    }
    compact = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["sha256"] = hashlib.sha256(compact.encode("utf-8")).hexdigest()
    return payload


def source_dependency_report() -> Dict[str, Any]:
    report = []
    for item in RULES:
        module = __import__(item.module, fromlist=["*"])
        function = getattr(module, item.function)
        report.append({
            "rule": item.name,
            "qualified_name": f"{item.module}.{item.function}",
            "signature": str(inspect.signature(function)),
            "source_file": inspect.getsourcefile(function),
            "source_line": inspect.getsourcelines(function)[1],
            "rng_injected": item.rng_injected,
        })
    return {"schema_version": "13.2.0", "rules": report}
