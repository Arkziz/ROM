"""Equipment Unit of Work over one canonical SQLite transaction."""
from __future__ import annotations
from rom_v2.infrastructure.persistence.equipment_repository import SQLiteEquipmentRepository
class SQLiteEquipmentUnitOfWork:
 def __init__(self,connection_factory):self._factory=connection_factory;self.connection=None;self.equipment=None
 def __enter__(self):self.connection=self._factory();self.connection.execute("BEGIN IMMEDIATE");self.equipment=SQLiteEquipmentRepository(self.connection);return self
 def commit(self):self.connection.commit()
 def rollback(self):self.connection.rollback()
 def __exit__(self,t,e,b):
  try:
   if t is not None:self.rollback()
  finally:self.connection.close()
class SQLiteEquipmentUnitOfWorkFactory:
 def __init__(self,connection_factory):self._factory=connection_factory
 def __call__(self):return SQLiteEquipmentUnitOfWork(self._factory)
