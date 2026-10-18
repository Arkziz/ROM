"""Focused V1-parity tests for resource lifecycle."""
import unittest
from rom_v2.domain.resource_lifecycle import *
class ResourceLifecycleTests(unittest.TestCase):
    def test_initialize_mana_and_non_mana(self):
        self.assertEqual(initialize_resources("mage",130,170),ResourceState(130,130,170,170))
        self.assertEqual(initialize_resources("warrior",130,170),ResourceState(130,130,0,0))
    def test_max_increase_preserves_current(self):
        old=ResourceState(75,130,40,170);self.assertEqual(synchronize_maximums(old,"mage",180,220),ResourceState(75,180,40,220))
    def test_max_decrease_clamps_current(self):
        old=ResourceState(120,130,160,170);self.assertEqual(synchronize_maximums(old,"mage",100,90),ResourceState(100,100,90,90))
    def test_non_mana_transition_zeroes_mp(self):
        old=ResourceState(80,130,100,170);self.assertEqual(synchronize_maximums(old,"warrior",130,170),ResourceState(80,130,0,0))
    def test_set_and_restore_are_bounded(self):
        state=ResourceState(50,130,20,170);state=set_current_resources(state,current_hp=999,current_mp=-1);self.assertEqual(state,ResourceState(130,130,0,170));self.assertEqual(restore_resources(state,hp_amount=20,mp_amount=500),ResourceState(130,130,170,170))
    def test_defeat_sets_one_hp(self):self.assertEqual(apply_pve_defeat(ResourceState(0,130,30,170)),ResourceState(1,130,30,170))
if __name__=='__main__':unittest.main()
