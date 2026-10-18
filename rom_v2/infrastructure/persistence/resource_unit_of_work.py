"""SQLite Unit-of-Work adapter for resource lifecycle."""
from __future__ import annotations
from types import TracebackType
from rom_v2.infrastructure.persistence.connection_factory import V2ConnectionFactory
from rom_v2.infrastructure.persistence.resource_repository import SQLiteResourceRepository
from rom_v2.infrastructure.persistence.unit_of_work import SQLiteUnitOfWork
class SQLiteResourceUnitOfWork:
    def __init__(self,factory:V2ConnectionFactory)->None:self._inner=SQLiteUnitOfWork(factory)
    def __enter__(self):self._inner.__enter__();self.resources=SQLiteResourceRepository(self._inner.connection);return self
    def commit(self)->None:self._inner.commit()
    def __exit__(self,exception_type:type[BaseException]|None,exception:BaseException|None,traceback:TracebackType|None)->bool:return self._inner.__exit__(exception_type,exception,traceback)
class SQLiteResourceUnitOfWorkFactory:
    def __init__(self,factory:V2ConnectionFactory)->None:self._factory=factory
    def __call__(self)->SQLiteResourceUnitOfWork:return SQLiteResourceUnitOfWork(self._factory)
