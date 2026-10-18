"""Tests for canonical ROM V2 character lifecycle."""
from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from rom_v2.application import CharacterResultStatus,CharacterService,CreateCharacterCommand,ResetCharacterCommand
from rom_v2.infrastructure.persistence import SQLiteCharacterUnitOfWorkFactory,V2ConnectionFactory,V2Migrator

class CharacterLifecycleTest(unittest.TestCase):
 def _service(self,d):
  root=Path(d)/".runtime"/"v2"/"db";db=root/"rom_v2.db";V2Migrator(db).recreate();factory=V2ConnectionFactory(db,runtime_root=root)
  c=factory.connect_read_write();c.execute("INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)");c.close();return factory,CharacterService(SQLiteCharacterUnitOfWorkFactory(factory))
 def test_create_and_idempotency(self):
  with tempfile.TemporaryDirectory() as d:
   _,s=self._service(d);one=s.create(CreateCharacterCommand("c","a","ValidName","warrior","start_path",130,100));two=s.create(CreateCharacterCommand("c2","a","OtherName","mage","start_path",100,120));self.assertEqual(one.status,CharacterResultStatus.CREATED);self.assertEqual(two.status,CharacterResultStatus.ALREADY_EXISTS);self.assertEqual(two.character.character_id,"c")
 def test_validation_without_name_examples(self):
  with tempfile.TemporaryDirectory() as d:
   factory,s=self._service(d)
   for name in (""," bad","bad\nname"):
    self.assertEqual(s.create(CreateCharacterCommand("c","a",name,"warrior","start_path",130,100)).status,CharacterResultStatus.REJECTED)
   c=factory.connect_read_only();self.assertEqual(c.execute("SELECT COUNT(*) FROM characters").fetchone()[0],0);c.close()
 def test_duplicate_name_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   factory,s=self._service(d);s.create(CreateCharacterCommand("c","a","UniqueName","warrior","start_path",130,100))
   c=factory.connect_read_write();c.execute("INSERT INTO accounts VALUES ('b',2,'active','2026-01-01T00:00:00Z',60,0)");c.close()
   result=s.create(CreateCharacterCommand("c2","b","UniqueName","mage","start_path",100,120));self.assertEqual(result.reason,"character_name_exists")
 def test_reset_preserves_identity_name_and_class(self):
  with tempfile.TemporaryDirectory() as d:
   _,s=self._service(d);created=s.create(CreateCharacterCommand("c","a","StableName","warrior","start_path",130,100)).character
   reset=s.reset(ResetCharacterCommand("c",created.version,"start_path",130,100));self.assertEqual(reset.status,CharacterResultStatus.RESET);self.assertEqual((reset.character.character_id,reset.character.name,reset.character.class_key),("c","StableName","warrior"));self.assertEqual((reset.character.level,reset.character.experience,reset.character.version),(1,0,1))
 def test_reset_version_conflict_and_resource_validation(self):
  with tempfile.TemporaryDirectory() as d:
   _,s=self._service(d);s.create(CreateCharacterCommand("c","a","StableName","warrior","start_path",130,100))
   self.assertEqual(s.reset(ResetCharacterCommand("c",1,"start_path",130,100)).reason,"character_version_conflict")
   self.assertEqual(s.reset(ResetCharacterCommand("c",0,"start_path",-1,100)).reason,"current_hp_invalid")
 def test_restart_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   factory,s=self._service(d);s.create(CreateCharacterCommand("c","a","StableName","warrior","start_path",130,100));reopened=CharacterService(SQLiteCharacterUnitOfWorkFactory(factory));self.assertEqual(reopened.create(CreateCharacterCommand("x","a","OtherName","mage","start_path",100,120)).character.character_id,"c")
if __name__=="__main__":unittest.main()
