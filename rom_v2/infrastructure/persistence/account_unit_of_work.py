"""Infrastructure adapter binding account repositories to the canonical SQLite UoW."""
from __future__ import annotations

from types import TracebackType

from rom_v2.infrastructure.persistence.account_repository import SQLiteAccountRepository
from rom_v2.infrastructure.persistence.connection_factory import V2ConnectionFactory
from rom_v2.infrastructure.persistence.unit_of_work import SQLiteUnitOfWork


class SQLiteAccountUnitOfWork:
    """Adapt the generic SQLite transaction to the account application port."""
    def __init__(self, connection_factory: V2ConnectionFactory) -> None:
        self._inner = SQLiteUnitOfWork(connection_factory)
        self.accounts: SQLiteAccountRepository

    def __enter__(self) -> SQLiteAccountUnitOfWork:
        self._inner.__enter__()
        self.accounts = SQLiteAccountRepository(self._inner.connection)
        return self

    def commit(self) -> None:
        self._inner.commit()

    def __exit__(self, exception_type: type[BaseException] | None, exception: BaseException | None, traceback: TracebackType | None) -> bool:
        return self._inner.__exit__(exception_type, exception, traceback)


class SQLiteAccountUnitOfWorkFactory:
    """Create one fresh account transaction adapter per application operation."""
    def __init__(self, connection_factory: V2ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def __call__(self) -> SQLiteAccountUnitOfWork:
        return SQLiteAccountUnitOfWork(self._connection_factory)
