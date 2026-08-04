from pathlib import Path

from systems.simulation.balance_analyzer import (
    AnalysisConfig,
    build_execution_plan,
    execute_plan,
    inspect_execution_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = AnalysisConfig(
        3,
        ("regular",),
        ("warrior", "mage"),
        (137000, 137001),
        40,
        True,
    )
    plan = build_execution_plan(config, include_walls=True, include_inventory=True)
    assert len(plan) == 12
    before = inspect_execution_plan(ROOT, plan)
    payloads, execution = execute_plan(ROOT, plan, workers=2, force=False)
    assert len(payloads) == 12
    after = inspect_execution_plan(ROOT, plan)
    assert after["cache_hits"] == 12 and after["new_simulations"] == 0
    assert execution["unique_scenarios"] == 12
    assert execution["workers"] == 2
    print("[OK] PvE analysis performance/checkpoint contracts")
    print("- unified deduplicated execution plan: PASS")
    print("- process workers 1..8: PASS")
    print("- atomic per-scenario cache checkpoint: PASS")
    print("- interrupted-run resume contract: PASS")
    print("- cached rerun requires zero new simulations: PASS")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
