"""Canonical SQLite repository for the ROM V2 character aggregate."""
from __future__ import annotations
import sqlite3
from rom_v2.domain.character import Character
from rom_v2.infrastructure.persistence.repository_base import SQLiteRepositoryBase

class SQLiteCharacterRepository(SQLiteRepositoryBase):
    @staticmethod
    def _map(row: sqlite3.Row) -> Character:
        return Character(str(row["character_id"]),str(row["account_id"]),str(row["name"]),str(row["class_key"]),int(row["level"]),int(row["experience"]),str(row["location_key"]),int(row["current_hp"]),None if row["current_mp"] is None else int(row["current_mp"]),int(row["version"]))
    def find_by_id(self, character_id: str) -> Character | None:
        row=self.fetch_one("SELECT * FROM characters WHERE character_id = ?",(character_id,)); return None if row is None else self._map(row)
    def find_by_account_id(self, account_id: str) -> Character | None:
        row=self.fetch_one("SELECT * FROM characters WHERE account_id = ?",(account_id,)); return None if row is None else self._map(row)
    def find_by_name(self, name: str) -> Character | None:
        row=self.fetch_one("SELECT * FROM characters WHERE name = ?",(name,)); return None if row is None else self._map(row)
    def add(self, character: Character) -> None:
        changed=self.execute("INSERT INTO characters(character_id,account_id,name,class_key,level,experience,location_key,current_hp,current_mp,version) VALUES (?,?,?,?,?,?,?,?,?,?)",(character.character_id,character.account_id,character.name,character.class_key,character.level,character.experience,character.location_key,character.current_hp,character.current_mp,character.version)); self.require_exact_rowcount(changed)
    def reset(self, character: Character, *, expected_version: int) -> None:
        changed=self.execute("UPDATE characters SET level=?,experience=?,location_key=?,current_hp=?,current_mp=?,version=? WHERE character_id=? AND version=?",(character.level,character.experience,character.location_key,character.current_hp,character.current_mp,character.version,character.character_id,expected_version)); self.require_exact_rowcount(changed)
