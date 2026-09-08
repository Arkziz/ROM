from systems.stat_system import (
    calculate_magical_attack,
    calculate_magical_defense,
    calculate_physical_attack,
    calculate_physical_defense,
)


def main():
    assert calculate_physical_attack("warrior", strength=30, dexterity=90) == 30
    assert calculate_physical_attack("knight", strength=30, dexterity=90) == 30
    assert calculate_physical_attack("rogue", strength=20, dexterity=30) == 27
    assert calculate_physical_attack("scout", strength=20, dexterity=30) == 27
    assert calculate_physical_attack("mage", strength=30) == 6
    assert calculate_magical_attack("mage", intelligence=30) == 30
    assert calculate_magical_attack("priest", intelligence=30) == 30
    assert calculate_magical_attack("warrior", intelligence=30) == 6
    assert calculate_physical_defense(equipment_pdef=10, stamina=25) == 18
    assert calculate_magical_defense(equipment_mdef=10, wisdom=25) == 18
    print("[PASS] Stage 18.15.8 combat-stat production switch contract")


if __name__ == "__main__":
    main()
