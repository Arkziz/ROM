from __future__ import annotations
import sqlite3, unittest
from rom_v2.domain.item import ItemDefinition,ItemInstance,StoryQuestItemIdentity
from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import BASELINE_SQL
from rom_v2.infrastructure.persistence.migrations.v002_primary_stats_parity import MIGRATION as M2
from rom_v2.infrastructure.persistence.migrations.v003_item_identity_parity import MIGRATION as M3
class ItemIdentityTest(unittest.TestCase):
 def test_domain_identity_is_separate(self):
  definition=ItemDefinition(42,"A","material",{})
  instance=ItemInstance(900,7,definition.item_id,3,{})
  self.assertEqual((definition.item_id,instance.inventory_id,instance.item_id),(42,900,42))
  self.assertNotEqual(instance.inventory_id,instance.item_id)
 def test_quest_identity_has_no_inventory_or_item_id(self):
  value=StoryQuestItemIdentity(7,11,"token")
  self.assertEqual((value.user_id,value.quest_id,value.item_key),(7,11,"token"))
  self.assertFalse(hasattr(value,"inventory_id")); self.assertFalse(hasattr(value,"item_id"))
 def test_forward_migration_contract(self):
  db=sqlite3.connect(":memory:"); db.execute("PRAGMA foreign_keys=ON")
  db.executescript(BASELINE_SQL); db.executescript(M2.sql); db.executescript(M3.sql)
  db.execute("INSERT INTO item_definitions(item_id,name,item_type) VALUES(1,'A','material')")
  db.execute("INSERT INTO inventory_items(inventory_id,owner_user_id,item_id,quantity) VALUES(101,7,1,2)")
  self.assertEqual(db.execute("SELECT inventory_id,item_id,quantity FROM inventory_items").fetchone(),(101,1,2))
  with self.assertRaises(sqlite3.IntegrityError): db.execute("DELETE FROM item_definitions WHERE item_id=1")
  db.close()
if __name__=='__main__': unittest.main()
