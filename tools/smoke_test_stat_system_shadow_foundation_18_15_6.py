from systems.stat_system import (
    calculate_magical_attack,
    calculate_magical_defense,
    calculate_max_hp,
    calculate_max_mp,
    calculate_physical_attack,
    calculate_physical_defense,
)


def main():
    assert calculate_physical_attack("warrior", strength=30, dexterity=999) == 30
    assert calculate_physical_attack("knight", strength=30, dexterity=999) == 30
    assert calculate_physical_attack("rogue", strength=20, dexterity=30) == 27
    assert calculate_physical_attack("scout", strength=20, dexterity=30) == 27
    assert calculate_physical_attack("mage", strength=30) == 6
    assert calculate_magical_attack("mage", intelligence=30) == 30
    assert calculate_magical_attack("priest", intelligence=30) == 30
    assert calculate_magical_attack("warrior", intelligence=30) == 6
    assert calculate_physical_defense(equipment_pdef=10, stamina=25) == 18
    assert calculate_magical_defense(equipment_mdef=10, wisdom=25) == 18
    assert calculate_physical_defense(equipment_pdef=0, stamina=10) == 3
    assert calculate_magical_defense(equipment_mdef=0, wisdom=10) == 3
    assert calculate_physical_defense(equipment_pdef=7, stamina=0) == 7
    assert calculate_magical_defense(equipment_mdef=9, wisdom=0) == 9
    assert calculate_max_hp(base_hp=100, stamina_hp=30, equipment_hp=20, refinement_hp=5) == 155
    assert calculate_max_mp("mage", level=1, intelligence=10, wisdom=10) == 170
    assert calculate_max_mp("priest", level=10, intelligence=30, wisdom=40) == 480
    assert calculate_max_mp("rogue", level=10, intelligence=999, wisdom=999) == 0
    base = calculate_max_mp("mage", level=10, intelligence=30, wisdom=30)
    assert calculate_max_mp("mage", level=10, intelligence=40, wisdom=30) - base == 20
    assert calculate_max_mp("mage", level=10, intelligence=30, wisdom=40) - base == 30
    assert calculate_max_mp("mage", level=11, intelligence=30, wisdom=30) - base == 20
    print("[PASS] Stage 18.15.6 stat-system shadow foundation")
    print("- Candidate F2 PATK/MATK: PASS")
    print("- WIS-focused Max MP 2/3: PASS")
    print("- Production runtime switch: NOT PERFORMED")


if __name__ == "__main__":
    main()
