"""Infrastructure adapter binding character repositories to the SQLite UoW."""
from __future__ import annotations
from types import TracebackType
from rom_v2.infrastructure.persistence.character_repository import SQLiteCharacterRepository
from rom_v2.infrastructure.persistence.connection_factory import V2ConnectionFactory
from rom_v2.infrastructure.persistence.unit_of_work import SQLiteUnitOfWork

class SQLiteCharacterUnitOfWork:
    def __init__(self, connection_factory: V2ConnectionFactory) -> None: self._inner=SQLiteUnitOfWork(connection_factory)
    def __enter__(self) -> SQLiteCharacterUnitOfWork:
        self._inner.__enter__(); self.characters=SQLiteCharacterRepository(self._inner.connection); return self
    def commit(self) -> None: self._inner.commit()
    def __exit__(self, exception_type:type[BaseException]|None, exception:BaseException|None, traceback:TracebackType|None)->bool: return self._inner.__exit__(exception_type,exception,traceback)
class SQLiteCharacterUnitOfWorkFactory:
    def __init__(self, connection_factory: V2ConnectionFactory) -> None: self._connection_factory=connection_factory
    def __call__(self) -> SQLiteCharacterUnitOfWork: return SQLiteCharacterUnitOfWork(self._connection_factory)
