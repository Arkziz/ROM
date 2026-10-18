"""Source-faithful tests for the audited ROM V1 class catalog parity."""
from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from rom_v2.application import CharacterResultStatus,CharacterService,CreateCharacterCommand
from rom_v2.domain import ClassCatalog,DEFAULT_CLASS_CATALOG
from rom_v2.infrastructure.persistence import SQLiteCharacterUnitOfWorkFactory,V2ConnectionFactory,V2Migrator

EXPECTED={
 "warrior":{"name":"🛡️ Воїн","resource":"rage","armor":"chain","main":("sword_1h","sword_2h"),"off":("warrior_shield",)},
 "knight":{"name":"⚔️ Лицар","resource":"rage","armor":"plate","main":("sword_1h",),"off":("shield",)},
 "scout":{"name":"🏹 Скаут","resource":"combat_energy","armor":"leather","main":("bow_2h","crossbow_2h"),"off":()},
 "rogue":{"name":"🗡️ Розбійник","resource":"combat_energy_combo","armor":"leather","main":("dagger_1h",),"off":("dagger",)},
 "mage":{"name":"🔮 Маг","resource":"mana","armor":"cloth","main":("wand_1h","staff_2h"),"off":("talisman",)},
 "priest":{"name":"⚕️ Жрець","resource":"mana","armor":"cloth","main":("wand_1h","staff_2h"),"off":("talisman",)},
}

class ClassCatalogTest(unittest.TestCase):
 def test_exact_audited_parity_matrix(self):
  self.assertEqual(tuple(EXPECTED),tuple(item.key for item in DEFAULT_CLASS_CATALOG.all()))
  for key,expected in EXPECTED.items():
   actual=DEFAULT_CLASS_CATALOG.require(key)
   self.assertEqual({"name":actual.display_name,"resource":actual.resource_key,"armor":actual.armor_type,"main":actual.main_hand_subtypes,"off":actual.off_hand_subtypes},expected)
 def test_forbidden_inventions_are_absent(self):
  self.assertNotIn("axe",DEFAULT_CLASS_CATALOG.require("warrior").main_hand_subtypes)
  self.assertNotIn("mace",DEFAULT_CLASS_CATALOG.require("knight").main_hand_subtypes)
  self.assertNotIn("dagger_1h",DEFAULT_CLASS_CATALOG.require("scout").main_hand_subtypes)
  self.assertNotIn("sword_1h",DEFAULT_CLASS_CATALOG.require("rogue").main_hand_subtypes)
  self.assertNotIn("mace",DEFAULT_CLASS_CATALOG.require("priest").main_hand_subtypes)
 def test_no_unaudited_attack_type_or_initial_stat_fields(self):
  definition=DEFAULT_CLASS_CATALOG.require("warrior")
  self.assertFalse(hasattr(definition,"attack_type"));self.assertFalse(hasattr(definition,"initial_stats"));self.assertFalse(hasattr(definition,"max_hp"))
 def test_unknown_key_rejected_before_database_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/"db";db=root/"rom_v2.db";V2Migrator(db).recreate();factory=V2ConnectionFactory(db,runtime_root=root);c=factory.connect_read_write();c.execute("INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)");c.close();service=CharacterService(SQLiteCharacterUnitOfWorkFactory(factory));result=service.create(CreateCharacterCommand("c","a","ValidName","unknown","start_path",130,100));self.assertEqual((result.status,result.reason),(CharacterResultStatus.REJECTED,"class_key_unknown"));c=factory.connect_read_only();self.assertEqual(c.execute("SELECT COUNT(*) FROM characters").fetchone()[0],0);c.close()
 def test_catalog_rejects_wrong_cardinality(self):
  with self.assertRaisesRegex(ValueError,"class_catalog_requires_six_classes"):ClassCatalog(DEFAULT_CLASS_CATALOG.all()[:5])
if __name__=="__main__":unittest.main()
