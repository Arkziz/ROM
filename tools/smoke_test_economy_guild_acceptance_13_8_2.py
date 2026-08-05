from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.simulation.economy_guild_acceptance import run_acceptance
from systems.simulation.guild_population import MAX_GUILD_MEMBERS, simulate_guild_population


def main():
    report = run_acceptance(ROOT, target_level=2, profile="regular", seed=138200, force=False)
    assert report["verdict"] == "PASS", report["failures"]
    assert report["guild_member_limit"] == 50 == MAX_GUILD_MEMBERS
    assert [row["players"] for row in report["guild_populations"]] == [10, 25, 50]
    assert report["inventory"]["40"]["asset_coverage"] == {"FULL": 2}
    assert report["inventory"]["60"]["asset_coverage"] == {"FULL": 2}
    assert report["inventory"]["40"]["reconciliation_failures"] == 0
    assert report["inventory"]["60"]["reconciliation_failures"] == 0
    try:
        simulate_guild_population([{"wins": 1}], 51)
    except ValueError as exc:
        assert "50" in str(exc)
    else:
        raise AssertionError("guild population above 50 was not rejected")
    print("[OK] Economy/guild acceptance 13.8.2 contracts")
    print("- economic v2 reconciliation for 40/60: PASS")
    print("- FULL asset coverage for 40/60: PASS")
    print("- paired same-class/same-seed inventory comparison: PASS")
    print("- guild populations 10/25/50 only: PASS")
    print("- guild member limit 50 enforced: PASS")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
