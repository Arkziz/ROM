"""SQLite repository for V1-faithful character lifecycle state."""
from __future__ import annotations
import sqlite3
from rom_v2.domain.character import Character,character_name_key
from rom_v2.infrastructure.persistence.repository_base import SQLiteRepositoryBase
class SQLiteCharacterRepository(SQLiteRepositoryBase):
 @staticmethod
 def _map(row:sqlite3.Row)->Character:return Character(str(row["character_id"]),str(row["account_id"]),str(row["name"]),str(row["class_key"]),int(row["level"]),int(row["experience"]),str(row["location_key"]),int(row["current_hp"]),None if row["current_mp"] is None else int(row["current_mp"]))
 def find_by_id(self,character_id:str)->Character|None:
  row=self.fetch_one("SELECT * FROM characters WHERE character_id = ?",(character_id,));return None if row is None else self._map(row)
 def find_by_account_id(self,account_id:str)->Character|None:
  row=self.fetch_one("SELECT * FROM characters WHERE account_id = ?",(account_id,));return None if row is None else self._map(row)
 def find_by_name_key(self,name_key:str)->Character|None:
  # V1 compares normalized names with casefold; SQLite NOCASE is insufficient for Unicode parity.
  rows=self.connection.execute("SELECT * FROM characters ORDER BY character_id").fetchall()
  for row in rows:
   if character_name_key(row["name"])==name_key:return self._map(row)
  return None
 def add(self,character:Character)->None:
  changed=self.execute("INSERT INTO characters(character_id,account_id,name,class_key,level,experience,location_key,current_hp,current_mp) VALUES (?,?,?,?,?,?,?,?,?)",(character.character_id,character.account_id,character.name,character.class_key,character.level,character.experience,character.location_key,character.current_hp,character.current_mp));self.require_exact_rowcount(changed)
 def delete(self,character_id:str)->None:
  changed=self.execute("DELETE FROM characters WHERE character_id = ?",(character_id,));self.require_exact_rowcount(changed)
