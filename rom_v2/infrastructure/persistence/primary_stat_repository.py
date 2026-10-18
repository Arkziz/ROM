"""SQLite repository for allocated primary stats and point invariants."""
from __future__ import annotations
import sqlite3
from rom_v2.domain.primary_stats import AttributePointState,PrimaryStats
from rom_v2.infrastructure.persistence.repository_base import SQLiteRepositoryBase
class SQLitePrimaryStatRepository(SQLiteRepositoryBase):
 @staticmethod
 def _map(row:sqlite3.Row)->AttributePointState:return AttributePointState(PrimaryStats(int(row["strength"]),int(row["dexterity"]),int(row["intelligence"]),int(row["wisdom"]),int(row["stamina"])),int(row["unspent_points"]),int(row["total_points_earned"]))
 def find(self,character_id:str)->AttributePointState|None:
  row=self.fetch_one("SELECT * FROM character_primary_stats WHERE character_id=?",(character_id,));return None if row is None else self._map(row)
 def add(self,character_id:str,state:AttributePointState)->None:
  changed=self.execute("INSERT INTO character_primary_stats(character_id,strength,dexterity,intelligence,wisdom,stamina,unspent_points,total_points_earned) VALUES(?,?,?,?,?,?,?,?)",(character_id,*state.allocated.values(),state.free_points,state.total_earned));self.require_exact_rowcount(changed)
 def replace(self,character_id:str,state:AttributePointState,expected_free_points:int)->None:
  changed=self.execute("UPDATE character_primary_stats SET strength=?,dexterity=?,intelligence=?,wisdom=?,stamina=?,unspent_points=?,total_points_earned=? WHERE character_id=? AND unspent_points=?",(*state.allocated.values(),state.free_points,state.total_earned,character_id,expected_free_points));self.require_exact_rowcount(changed)
