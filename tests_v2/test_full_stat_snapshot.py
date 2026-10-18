"""Focused V1-parity tests for the canonical full stat snapshot."""
import unittest

from rom_v2.application.full_stat_snapshot_service import FullStatSnapshotService
from rom_v2.domain.full_stat_snapshot import (
    DerivedBonusLayer,
    EquippedStatInput,
    FullStatSnapshotInput,
    build_full_stat_snapshot,
)
from rom_v2.domain.primary_stats import PrimaryStats


class FullStatSnapshotTests(unittest.TestCase):
    def test_source_layers_remain_visible_and_sum_once(self):
        source = FullStatSnapshotInput(
            class_key="mage",
            level=1,
            allocated=PrimaryStats(int=2, wis=1),
            equipment=(EquippedStatInput("eq-1", primary=PrimaryStats(int=3, sta=2)),),
            runes=PrimaryStats(wis=4),
        )
        snapshot = build_full_stat_snapshot(source)
        self.assertEqual(snapshot.base, PrimaryStats(10, 10, 10, 10, 10))
        self.assertEqual(snapshot.total_primary, PrimaryStats(10, 10, 15, 15, 12))

    def test_broken_and_unequipped_items_do_not_contribute(self):
        source = FullStatSnapshotInput(
            class_key="warrior",
            level=1,
            equipment=(
                EquippedStatInput("active", primary=PrimaryStats(str=2), derived=DerivedBonusLayer(pdef=3)),
                EquippedStatInput("broken", primary=PrimaryStats(str=99), durability=0),
                EquippedStatInput("bag", primary=PrimaryStats(str=88), equipped=False),
            ),
        )
        snapshot = build_full_stat_snapshot(source)
        self.assertEqual(snapshot.equipment, PrimaryStats(str=2))
        self.assertEqual(snapshot.equipment_derived.pdef, 3)

    def test_runes_are_primary_input_not_implicit_equipment_mutation(self):
        source = FullStatSnapshotInput(class_key="scout", level=1, runes=PrimaryStats(dex=5))
        snapshot = build_full_stat_snapshot(source)
        self.assertEqual(snapshot.equipment, PrimaryStats())
        self.assertEqual(snapshot.runes, PrimaryStats(dex=5))
        self.assertEqual(snapshot.total_primary.dex, 15)

    def test_enhancement_output_is_separate_and_applied_once(self):
        source = FullStatSnapshotInput(
            class_key="knight",
            level=1,
            equipment=(EquippedStatInput("armor", derived=DerivedBonusLayer(hp=10, pdef=4)),),
            enhancement=DerivedBonusLayer(hp=5, pdef=2),
        )
        snapshot = build_full_stat_snapshot(source)
        self.assertEqual(snapshot.equipment_derived, DerivedBonusLayer(hp=10, pdef=4))
        self.assertEqual(snapshot.enhancement_derived, DerivedBonusLayer(hp=5, pdef=2))
        self.assertEqual(snapshot.derived.max_hp, 145)
        self.assertEqual(snapshot.derived.pdef, 9)

    def test_non_mana_class_does_not_gain_equipment_mp(self):
        source = FullStatSnapshotInput(
            class_key="warrior",
            level=1,
            equipment=(EquippedStatInput("mp-item", derived=DerivedBonusLayer(mp=100)),),
        )
        self.assertEqual(build_full_stat_snapshot(source).derived.max_mp, 0)

    def test_three_consumers_receive_identical_snapshot(self):
        source = FullStatSnapshotInput(class_key="priest", level=2, allocated=PrimaryStats(wis=2))
        service = FullStatSnapshotService()
        self.assertEqual(service.for_profile(source), service.for_combat(source))
        self.assertEqual(service.for_combat(source), service.for_simulator(source))

    def test_duplicate_inventory_input_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate_equipment_inventory_id"):
            FullStatSnapshotInput(
                class_key="warrior",
                level=1,
                equipment=(EquippedStatInput("same"), EquippedStatInput("same")),
            )


if __name__ == "__main__":
    unittest.main()
