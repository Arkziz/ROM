import importlib
import unittest
from dataclasses import FrozenInstanceError
from rom_v2.content.world_graph import *

class WorldGraphTest(unittest.TestCase):
    def test_exact_nodes_metadata_duration_and_no_requirements(self):
        self.assertEqual(WORLD_NODE_ORDER, ("city", "start_path", "dark_forest"))
        self.assertEqual(tuple(WORLD_NODES), WORLD_NODE_ORDER)
        self.assertEqual(TRAVEL_SECONDS, 20)
        self.assertEqual(TRANSPORT_REQUIREMENTS, ())
        self.assertEqual((WORLD_NODES["city"].kind, WORLD_NODES["city"].huntable), ("city", False))
        self.assertEqual((WORLD_NODES["start_path"].kind, WORLD_NODES["start_path"].huntable), ("location", True))
        self.assertEqual((WORLD_NODES["dark_forest"].kind, WORLD_NODES["dark_forest"].huntable), ("location", True))
    def test_exact_symmetric_connected_graph(self):
        self.assertEqual(get_adjacent_nodes("city"), ("start_path",))
        self.assertEqual(get_adjacent_nodes("start_path"), ("city", "dark_forest"))
        self.assertEqual(get_adjacent_nodes("dark_forest"), ("start_path",))
        self.assertTrue(are_adjacent("city", "start_path"))
        self.assertTrue(are_adjacent("start_path", "dark_forest"))
        self.assertFalse(are_adjacent("city", "dark_forest"))
        self.assertFalse(are_adjacent("dark_forest", "city"))
    def test_unknown_queries_fail_closed_without_fallback(self):
        self.assertIsNone(get_world_node("unknown_zone"))
        self.assertEqual(get_adjacent_nodes("unknown_zone"), ())
        self.assertFalse(are_adjacent("unknown_zone", "city"))
        self.assertFalse(are_adjacent("city", "unknown_zone"))
        self.assertIsNone(get_world_node(""))
    def test_immutable_and_restart_stable(self):
        with self.assertRaises(TypeError):
            WORLD_NODES["x"] = get_world_node("city")  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            WORLD_NODES["city"].name = "x"  # type: ignore[misc]
        def snapshot(module):
            return (
                module.WORLD_NODE_ORDER,
                tuple((key, node.node_id, node.name, node.kind, node.huntable)
                      for key, node in module.WORLD_NODES.items()),
                tuple(module.LOCATION_GRAPH.items()),
                module.TRAVEL_SECONDS,
                module.TRANSPORT_REQUIREMENTS,
            )
        module = importlib.import_module("rom_v2.content.world_graph")
        before = snapshot(module)
        module = importlib.reload(module)
        self.assertEqual(before, snapshot(module))
    def test_referential_validation_against_location_catalog(self):
        self.assertIsNone(validate_world_graph(location_ids={"start_path", "dark_forest"}))
        with self.assertRaises(ValueError):
            validate_world_graph(location_ids={"start_path"})
        with self.assertRaises(ValueError):
            validate_world_graph(location_ids={"start_path", "dark_forest", "third"})
    def test_definition_validation(self):
        self.assertIsNone(validate_world_graph())

if __name__ == "__main__": unittest.main()
