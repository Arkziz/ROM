from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from rom_v2.application import CharacterResultStatus,CharacterService,CreateCharacterCommand,ResetCharacterCommand
from rom_v2.domain import normalize_character_name,validate_character_name
from rom_v2.infrastructure.persistence import SQLiteCharacterUnitOfWorkFactory,V2ConnectionFactory,V2Migrator
class CharacterLifecycleTest(unittest.TestCase):
 def _service(self,d):
  root=Path(d)/"db";db=root/"rom_v2.db";V2Migrator(db).recreate();f=V2ConnectionFactory(db,runtime_root=root);c=f.connect_read_write();c.execute("INSERT INTO accounts(account_id,telegram_user_id,registered_at_utc,bag_capacity) VALUES('a',1,'2026-01-01T00:00:00Z',60)");c.close();return f,CharacterService(SQLiteCharacterUnitOfWorkFactory(f))
 def test_v1_name_normalization_and_bounds(self):
  self.assertEqual(normalize_character_name("  А  Б  "),"А Б");self.assertEqual(validate_character_name("  А  Б  "),"А Б")
  for bad in ("А","1"*24,"А"*25,"Тестё"):
   with self.assertRaises(ValueError):validate_character_name(bad)
 def test_casefold_uniqueness(self):
  with tempfile.TemporaryDirectory() as d:
   f,s=self._service(d);self.assertEqual(s.create(CreateCharacterCommand("c","a","Тест","warrior","start_path",130,100)).status,CharacterResultStatus.CREATED);c=f.connect_read_write();c.execute("INSERT INTO accounts(account_id,telegram_user_id,registered_at_utc,bag_capacity) VALUES('b',2,'2026-01-01T00:00:00Z',60)");c.close();self.assertEqual(s.create(CreateCharacterCommand("d","b","тест","mage","start_path",130,100)).reason,"character_name_exists")
 def test_reset_removes_character_and_requires_registration(self):
  with tempfile.TemporaryDirectory() as d:
   f,s=self._service(d);s.create(CreateCharacterCommand("c","a","Тест","warrior","start_path",130,100));result=s.reset(ResetCharacterCommand("c"));self.assertEqual((result.status,result.character),(CharacterResultStatus.RESET,None));c=f.connect_read_only();self.assertEqual(c.execute("SELECT COUNT(*) FROM characters").fetchone()[0],0);self.assertEqual(c.execute("SELECT bag_capacity FROM accounts WHERE account_id='a'").fetchone()[0],60);c.close()
 def test_no_character_version_contract(self):
  from rom_v2.domain.character import Character
  x=Character("c","a","Тест","warrior",1,0,"start_path",130,100);self.assertFalse(hasattr(x,"version"))
if __name__=="__main__":unittest.main()
