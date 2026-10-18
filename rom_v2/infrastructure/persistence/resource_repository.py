"""SQLite adapter for current HP/MP persistence."""
from __future__ import annotations
from rom_v2.domain.resource_lifecycle import ResourceState
from rom_v2.infrastructure.persistence.repository_base import SQLiteRepositoryBase
class SQLiteResourceRepository(SQLiteRepositoryBase):
    def get(self,character_id:str,max_hp:int,max_mp:int)->ResourceState|None:
        row=self.fetch_one("SELECT current_hp,current_mp FROM characters WHERE character_id = ?",(character_id,))
        if row is None:return None
        hp_max=max(1,int(max_hp));mp_max=max(0,int(max_mp));raw_mp=0 if row["current_mp"] is None else int(row["current_mp"])
        return ResourceState(max(0,min(int(row["current_hp"]),hp_max)),hp_max,max(0,min(raw_mp,mp_max)),mp_max)
    def save_current(self,character_id:str,state:ResourceState)->None:
        affected=self.execute("UPDATE characters SET current_hp = ?, current_mp = ? WHERE character_id = ?",(state.current_hp,state.current_mp,character_id))
        self.require_exact_rowcount(affected)
