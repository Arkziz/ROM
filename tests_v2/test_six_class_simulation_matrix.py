from __future__ import annotations
import unittest
from rom_v2.domain.six_class_simulation_matrix import *

class FakePort:
    def __init__(self): self.created=[]; self.turn_calls=[]
    def create_character(self,class_key): self.created.append(class_key); return {"class":class_key}
    def stat_snapshot(self,c): return {"owner":"production_stats","class":c["class"]}
    def equipment_compatibility(self,c): return {"owner":"production_equipment","class":c["class"]}
    def skill_loadout(self,c): return (f"production_skill::{c['class']}",)
    def encounter_setup(self,c): return {"owner":"production_combat","class":c["class"]}
    def controlled_turns(self,c,*,maximum_turns):
        self.turn_calls.append((c["class"],maximum_turns)); return {"turns_executed":maximum_turns,"outcome":"probe_only"}

class MatrixTests(unittest.TestCase):
    def test_exact_six_class_order_and_no_long_run(self):
        port=FakePort(); result=SixClassSimulationMatrix(port).run_contract_probes(maximum_turns=1)
        self.assertEqual(result.class_keys,("warrior","knight","scout","rogue","mage","priest"))
        self.assertTrue(result.complete); self.assertFalse(result.long_run_executed)
        self.assertEqual(len(port.turn_calls),6)
    def test_zero_turn_setup_probe(self):
        port=FakePort(); result=SixClassSimulationMatrix(port).run_contract_probes(maximum_turns=0)
        self.assertEqual([x.controlled_turns_executed for x in result.results],[0]*6)
        self.assertEqual(port.turn_calls,[]); self.assertTrue(result.complete)
    def test_long_run_turn_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"between_0_and_3"):
            SixClassSimulationMatrix(FakePort()).run_contract_probes(maximum_turns=4)
    def test_each_class_uses_same_production_adapter_boundary(self):
        port=FakePort(); result=SixClassSimulationMatrix(port).run_contract_probes()
        for item in result.results:
            self.assertEqual(item.details["stats"]["owner"],"production_stats")
            self.assertEqual(item.details["equipment"]["owner"],"production_equipment")
            self.assertEqual(item.details["encounter"]["owner"],"production_combat")
    def test_invalid_adapter_turn_count_fails_closed(self):
        class Bad(FakePort):
            def controlled_turns(self,c,*,maximum_turns): return {"turns_executed":99}
        with self.assertRaisesRegex(ValueError,"invalid_controlled_turn_count"):
            SixClassSimulationMatrix(Bad()).run_contract_probes()

if __name__=="__main__": unittest.main()
