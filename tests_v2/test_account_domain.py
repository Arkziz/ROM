"""Tests for canonical ROM V2 account domain and application lifecycle."""
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from rom_v2.application import AccountResultStatus, AccountService, ChangeAccountStatusCommand, RegisterAccountCommand
from rom_v2.domain import Account, AccountStatus
from rom_v2.infrastructure.persistence import SQLiteAccountUnitOfWorkFactory, V2ConnectionFactory, V2Migrator

class AccountDomainTest(unittest.TestCase):
    def _service(self, directory: str):
        root=Path(directory)/".runtime"/"v2"/"db"; db=root/"rom_v2.db"; V2Migrator(db).recreate()
        factory=V2ConnectionFactory(db,runtime_root=root); return factory,AccountService(SQLiteAccountUnitOfWorkFactory(factory))
    def test_registration_creates_account_and_zero_wallet_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            factory,service=self._service(d); result=service.register(RegisterAccountCommand("a",1,"2026-01-01T00:00:00Z"))
            self.assertEqual(result.status,AccountResultStatus.CREATED)
            c=factory.connect_read_only(); self.assertEqual(c.execute("SELECT balance FROM crystal_wallets WHERE account_id='a'").fetchone()[0],0); c.close()
    def test_registration_is_idempotent_by_telegram_identity(self):
        with tempfile.TemporaryDirectory() as d:
            _,service=self._service(d); one=service.register(RegisterAccountCommand("a",1,"2026-01-01T00:00:00Z")); two=service.register(RegisterAccountCommand("b",1,"2026-01-01T00:00:01Z"))
            self.assertEqual(one.status,AccountResultStatus.CREATED); self.assertEqual(two.status,AccountResultStatus.ALREADY_EXISTS); self.assertEqual(two.account.account_id,"a")
    def test_invalid_identity_and_non_utc_time_are_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            factory,service=self._service(d)
            self.assertEqual(service.register(RegisterAccountCommand("a",0,"2026-01-01T00:00:00Z")).status,AccountResultStatus.REJECTED)
            self.assertEqual(service.register(RegisterAccountCommand("a",1,"2026-01-01T00:00:00")).status,AccountResultStatus.REJECTED)
            c=factory.connect_read_only(); self.assertEqual(c.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],0); c.close()
    def test_status_lifecycle_and_optimistic_version(self):
        with tempfile.TemporaryDirectory() as d:
            _,service=self._service(d); service.register(RegisterAccountCommand("a",1,"2026-01-01T00:00:00Z"))
            blocked=service.change_status(ChangeAccountStatusCommand("a",AccountStatus.BLOCKED,0)); self.assertEqual(blocked.account.version,1)
            stale=service.change_status(ChangeAccountStatusCommand("a",AccountStatus.ACTIVE,0)); self.assertEqual(stale.reason,"account_version_conflict")
            closed=service.change_status(ChangeAccountStatusCommand("a",AccountStatus.CLOSED,1)); self.assertEqual(closed.account.status,AccountStatus.CLOSED)
            forbidden=service.change_status(ChangeAccountStatusCommand("a",AccountStatus.ACTIVE,2)); self.assertEqual(forbidden.reason,"account_status_transition_forbidden")
    def test_domain_boundaries(self):
        with self.assertRaisesRegex(ValueError,"bag_capacity_out_of_range"): Account("a",1,AccountStatus.ACTIVE,"2026-01-01T00:00:00Z",0)
    def test_restart_recovery_reads_same_account(self):
        with tempfile.TemporaryDirectory() as d:
            factory,service=self._service(d); service.register(RegisterAccountCommand("a",1,"2026-01-01T00:00:00Z")); reopened=AccountService(SQLiteAccountUnitOfWorkFactory(factory))
            result=reopened.register(RegisterAccountCommand("b",1,"2026-01-01T00:00:01Z")); self.assertEqual(result.account.account_id,"a")
if __name__=="__main__": unittest.main()
