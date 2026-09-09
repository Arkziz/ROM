from __future__ import annotations

from data.stat_system_config import (
    MAGICAL_ATTACK_SCALING,
    MAX_MP_SCALING,
    PHYSICAL_ATTACK_SCALING,
    PRIMARY_STAT_KEYS,
    SUPPORTED_CLASSES,
    validate_stat_system_config,
)
from systems.stat_system import (
    calculate_magical_attack,
    calculate_max_mp,
    calculate_physical_attack,
)


def main():
    assert validate_stat_system_config() == ()
    assert set(PHYSICAL_ATTACK_SCALING) == set(SUPPORTED_CLASSES)
    assert set(MAGICAL_ATTACK_SCALING) == set(SUPPORTED_CLASSES)
    assert all(set(row) == set(PRIMARY_STAT_KEYS) for row in PHYSICAL_ATTACK_SCALING.values())
    assert all(set(row) == set(PRIMARY_STAT_KEYS) for row in MAGICAL_ATTACK_SCALING.values())
    assert MAX_MP_SCALING == {"base": 100.0, "level": 20.0, "int": 1.0, "wis": 4.0}

    stats = dict(strength=10, dexterity=10, intelligence=10, wisdom=10, stamina=10)
    expected_primary = {"warrior": 12, "knight": 12, "rogue": 12, "scout": 12, "mage": 12, "priest": 12}
    for class_key, expected in expected_primary.items():
        actual = (
            calculate_physical_attack(class_key, **stats)
            if class_key in {"warrior", "knight", "rogue", "scout"}
            else calculate_magical_attack(class_key, **stats)
        )
        assert actual == expected, (class_key, actual, expected)

    assert calculate_physical_attack("warrior", strength=30, dexterity=20) == 34
    assert calculate_physical_attack("knight", strength=30, dexterity=20) == 35
    assert calculate_physical_attack("scout", strength=30, dexterity=20) == 30
    assert calculate_physical_attack("rogue", strength=30, dexterity=20) == 28
    assert calculate_magical_attack("mage", intelligence=30, wisdom=20) == 34
    assert calculate_magical_attack("priest", intelligence=30, wisdom=20) == 33
    assert calculate_magical_attack("warrior", intelligence=30, wisdom=999) == 6
    assert calculate_physical_attack("mage", strength=30, dexterity=999) == 6
    assert calculate_physical_attack("unknown", strength=999, dexterity=999) == 0
    assert calculate_magical_attack("unknown", intelligence=999, wisdom=999) == 0

    assert calculate_max_mp("mage", level=1, intelligence=10, wisdom=10) == 170
    assert calculate_max_mp("priest", level=10, intelligence=30, wisdom=40) == 490
    base = calculate_max_mp("mage", level=10, intelligence=30, wisdom=30)
    assert calculate_max_mp("mage", level=10, intelligence=40, wisdom=30) - base == 10
    assert calculate_max_mp("mage", level=10, intelligence=30, wisdom=40) - base == 40
    assert calculate_max_mp("mage", level=11, intelligence=30, wisdom=30) - base == 20
    assert calculate_max_mp("rogue", level=50, intelligence=999, wisdom=999) == 0
    print("[PASS] configurable PATK/MATK and Max-MP scaling contracts")


if __name__ == "__main__":
    main()
