"""Parity tests for the audited derived-stat engine."""
import unittest
from rom_v2.domain.derived_stats import *
class DerivedStatsTests(unittest.TestCase):
 def test_starting_hp(self): self.assertEqual(calculate_max_hp(1,10),130)
 def test_attacks(self):
  s={'str':30,'dex':20,'int':30,'wis':20,'sta':10}
  self.assertEqual([calculate_patk(k,s) for k in ('warrior','knight','scout','rogue')],[34,35,30,28])
  self.assertEqual([calculate_matk(k,s) for k in ('mage','priest')],[34,33])
 def test_mp(self):
  self.assertEqual(calculate_max_mp('mage',1,10,10),170); self.assertEqual(calculate_max_mp('warrior',1,10,10),0)
 def test_defense(self): self.assertEqual(calculate_pdef(10,25),18); self.assertEqual(calculate_mdef(0,10),3)
 def test_crit_and_dodge(self):
  self.assertEqual(calculate_physical_crit(10),5.0); self.assertEqual(calculate_magical_crit(50),19.0)
  self.assertEqual(calculate_dodge(10,30),1.0); self.assertEqual(calculate_dodge(50,10),13.0)
if __name__=='__main__': unittest.main()
