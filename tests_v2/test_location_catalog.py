import importlib
import unittest
from dataclasses import FrozenInstanceError
from rom_v2.content.location_catalog import *

class LocationCatalogTest(unittest.TestCase):
    def test_exact_two_location_identity_order_and_levels(self):
        self.assertEqual(LOCATION_ORDER,("start_path","dark_forest"))
        self.assertEqual(tuple(LOCATIONS),LOCATION_ORDER)
        self.assertEqual(len(LOCATIONS),2)
        start=require_location("start_path"); dark=require_location("dark_forest")
        self.assertEqual((start.name,start.level_min,start.level_max,start.unlock_level),("🌿 Початок Шляху",1,5,1))
        self.assertEqual((dark.name,dark.level_min,dark.level_max,dark.unlock_level),("🌲 Темний Бір",6,10,6))
        self.assertEqual(len(start.mob_names),10); self.assertEqual(len(dark.mob_names),10)
        self.assertEqual(start.boss_name,"🐺 Ватажок зграї"); self.assertEqual(dark.boss_name,"👑 Король Гоблінів")
    def test_immutable_and_restart_stable(self):
        with self.assertRaises(TypeError): LOCATIONS["x"]=require_location("start_path")  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError): require_location("start_path").name="x"  # type: ignore[misc]
        def snapshot(module):
            return (
                module.LOCATION_ORDER,
                tuple((key, location.location_id, location.name, location.description,
                       location.level_min, location.level_max, location.unlock_level,
                       location.boss_name, location.mob_names)
                      for key, location in module.LOCATIONS.items()),
            )
        module=importlib.import_module("rom_v2.content.location_catalog")
        before=snapshot(module)
        module=importlib.reload(module)
        after=snapshot(module)
        self.assertEqual(before,after)
    def test_unknown_ids_fail_closed_and_never_leak(self):
        self.assertIsNone(get_location("unknown_zone"))
        for call in (
            lambda: require_location("unknown_zone"),
            lambda: get_location_display_name("unknown_zone"),
        ):
            with self.assertRaises(KeyError):
                call()
    def test_unlock_boundaries_and_order(self):
        self.assertEqual(tuple(x.location_id for x in get_unlocked_locations(1)),("start_path",))
        self.assertEqual(tuple(x.location_id for x in get_unlocked_locations(5)),("start_path",))
        self.assertEqual(tuple(x.location_id for x in get_unlocked_locations(6)),("start_path","dark_forest"))
        self.assertTrue(is_location_unlocked("start_path",1)); self.assertFalse(is_location_unlocked("dark_forest",5)); self.assertTrue(is_location_unlocked("dark_forest",6))
        for invalid in (0,-1,True,1.0,"6"):
            with self.assertRaises(ValueError): get_unlocked_locations(invalid)  # type: ignore[arg-type]
    def test_catalog_validation(self):
        self.assertIsNone(validate_location_catalog())

if __name__ == "__main__": unittest.main()
