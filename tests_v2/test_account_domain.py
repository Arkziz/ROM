from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from rom_v2.application import AccountResultStatus,AccountService,RegisterAccountCommand
from rom_v2.infrastructure.persistence import SQLiteAccountUnitOfWorkFactory,V2ConnectionFactory,V2Migrator
class AccountDomainTest(unittest.TestCase):
 def test_registration_and_replay(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/"db";db=root/"rom_v2.db";V2Migrator(db).recreate();f=V2ConnectionFactory(db,runtime_root=root);s=AccountService(SQLiteAccountUnitOfWorkFactory(f));cmd=RegisterAccountCommand("a",1,"2026-01-01T00:00:00Z",60);self.assertEqual(s.register(cmd).status,AccountResultStatus.CREATED);self.assertEqual(s.register(cmd).status,AccountResultStatus.ALREADY_EXISTS);c=f.connect_read_only();self.assertEqual(c.execute("SELECT balance FROM crystal_wallets").fetchone()[0],0);c.close()
 def test_no_invented_status_or_version_contract(self):
  from rom_v2.domain.account import Account
  a=Account("a",1,"2026-01-01T00:00:00Z",60);self.assertFalse(hasattr(a,"status"));self.assertFalse(hasattr(a,"version"));self.assertFalse(hasattr(a,"change_status"))
if __name__=="__main__":unittest.main()
