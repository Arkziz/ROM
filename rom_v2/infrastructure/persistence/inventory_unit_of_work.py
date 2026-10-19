"""Inventory Unit of Work using the canonical SQLite connection factory."""
from __future__ import annotations
from rom_v2.infrastructure.persistence.inventory_repository import SQLiteInventoryRepository
class SQLiteInventoryUnitOfWork:
    def __init__(self,connection_factory): self._factory=connection_factory; self.connection=None; self.inventory=None
    def __enter__(self):
        self.connection=self._factory(); self.connection.execute("BEGIN IMMEDIATE"); self.inventory=SQLiteInventoryRepository(self.connection); return self
    def commit(self): self.connection.commit()
    def rollback(self): self.connection.rollback()
    def __exit__(self,exc_type,exc,tb):
        try:
            if exc_type is not None: self.rollback()
        finally: self.connection.close()
class SQLiteInventoryUnitOfWorkFactory:
    def __init__(self,connection_factory): self._factory=connection_factory
    def __call__(self): return SQLiteInventoryUnitOfWork(self._factory)
