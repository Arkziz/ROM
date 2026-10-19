import sqlite3, unittest
from rom_v2.application.inventory_service import InventoryService
from rom_v2.infrastructure.persistence.inventory_unit_of_work import SQLiteInventoryUnitOfWorkFactory
from rom_v2.infrastructure.persistence.migrations.v003_item_identity_parity import MIGRATION_SQL
class Factory:
 def __init__(self):
  self.db=sqlite3.connect(":memory:"); self.db.executescript(MIGRATION_SQL); self.db.execute("INSERT INTO item_definitions VALUES(1,'Potion','consumable','{}')"); self.db.commit()
 def __call__(self):
  # shared in-memory DB needs proxy connection semantics for focused repository test
  return self.db
class NoReservations:
 def reserved_quantity(self,*_): return 0
class InventoryServiceTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:"); self.db.executescript(MIGRATION_SQL); self.db.execute("INSERT INTO item_definitions VALUES(1,'Potion','consumable','{}')"); self.db.commit()
  class Uow:
   def __init__(u):
    from rom_v2.infrastructure.persistence.inventory_repository import SQLiteInventoryRepository
    u.connection=self.db; u.inventory=SQLiteInventoryRepository(self.db)
   def __enter__(u): u.connection.execute('BEGIN IMMEDIATE'); return u
   def commit(u): u.connection.commit()
   def rollback(u): u.connection.rollback()
   def __exit__(u,t,e,b):
    if t: u.rollback()
  self.service=InventoryService(Uow,NoReservations())
 def tearDown(self): self.db.close()
 def test_stack_capacity_and_consumption(self):
  r=self.service.add_item(1,1,7,2,5); self.assertEqual(r.status,'ok'); self.assertEqual([x.quantity for x in self.service.list_inventory(1).instances],[5,2])
  self.assertEqual(self.service.consume_by_definition(1,1,6).status,'ok'); self.assertEqual([x.quantity for x in self.service.list_inventory(1).instances],[1])
 def test_capacity_fail_closed(self): self.assertEqual(self.service.add_item(1,1,6,1,5).reason,'inventory_capacity_exceeded')
