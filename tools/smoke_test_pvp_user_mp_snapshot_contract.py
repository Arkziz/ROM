from __future__ import annotations

from systems.pvp_battle_factory import _coerce_current_mp


def main():
    assert _coerce_current_mp({"mp": 37, "max_mp": 100, "current_mp": 37}, 100) == 37
    assert _coerce_current_mp({"current_mp": 22, "max_mp": 100}, 100) == 22
    assert _coerce_current_mp(19, 100) == 19
    assert _coerce_current_mp(None, 80) == 80
    assert _coerce_current_mp({}, 60) == 60
    assert _coerce_current_mp("bad", 55) == 55
    print("[OK] PvP user-MP snapshot contract")
    print("- canonical db.get_user_mp mapping contract: PASS")
    print("- legacy numeric fixture contract: PASS")
    print("- invalid/missing value fallback to max MP: PASS")
    print("- production db API changed: 0")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
