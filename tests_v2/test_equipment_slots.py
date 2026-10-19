import sqlite3,unittest
from rom_v2.application.equipment_service import EquipmentService
from rom_v2.domain.equipment import EquipmentItemPolicy,SLOT_KEYS
from rom_v2.infrastructure.persistence.equipment_repository import SQLiteEquipmentRepository
from rom_v2.infrastructure.persistence.migrations.v003_item_identity_parity import MIGRATION as MIGRATION_003
from rom_v2.infrastructure.persistence.migrations.v004_equipment_slots_parity import MIGRATION_SQL as M4
class EquipmentTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:");self.db.executescript(MIGRATION_003.sql);self.db.executescript(M4);self.db.execute("INSERT INTO item_definitions VALUES(1,'Sword','equipment','{}')");self.db.execute("INSERT INTO inventory_items(owner_user_id,item_id,quantity,instance_metadata_json) VALUES(1,1,1,'{}')");self.db.execute("INSERT INTO inventory_items(owner_user_id,item_id,quantity,instance_metadata_json) VALUES(1,1,1,'{}')");self.db.commit()
  outer=self
  class U:
   def __enter__(u):u.c=outer.db;u.c.execute('BEGIN IMMEDIATE');u.equipment=SQLiteEquipmentRepository(u.c);return u
   def commit(u):u.c.commit()
   def rollback(u):u.c.rollback()
   def __exit__(u,t,e,b):
    if t:u.rollback()
  self.s=EquipmentService(U)
 def tearDown(self):self.db.close()
 def test_taxonomy_exact(self):self.assertEqual(len(SLOT_KEYS),10)
 def test_exact_identity_replacement_and_two_hand(self):
  self.assertEqual(self.s.equip(EquipmentItemPolicy(2,1,'off_hand'),1,'warrior').status,'ok')
  r=self.s.equip(EquipmentItemPolicy(1,1,'main_hand',weapon_hands=2),1,'warrior');self.assertEqual(r.status,'ok');self.assertEqual(r.displaced,(2,));self.assertEqual([x.slot_key for x in r.slots],['main_hand'])
 def test_class_and_level_fail_closed(self):
  self.assertEqual(self.s.equip(EquipmentItemPolicy(1,1,'main_hand',required_level=2),1,'warrior').reason,'required_level_not_met')
  self.assertEqual(self.s.equip(EquipmentItemPolicy(1,1,'main_hand',allowed_classes=('mage',)),2,'warrior').reason,'class_incompatible')
 def test_foreign_inventory_rejected(self):self.assertEqual(self.s.equip(EquipmentItemPolicy(1,2,'main_hand'),1,'warrior').reason,'inventory_instance_not_found')
