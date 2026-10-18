"""Character aggregate and lifecycle validation for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass, replace

@dataclass(frozen=True, slots=True)
class Character:
    """Represent persistent character identity, progression, location, and current resources."""
    character_id: str
    account_id: str
    name: str
    class_key: str
    level: int
    experience: int
    location_key: str
    current_hp: int
    current_mp: int | None
    version: int = 0

    def __post_init__(self) -> None:
        if not self.character_id.strip(): raise ValueError("character_id_required")
        if not self.account_id.strip(): raise ValueError("account_id_required")
        normalized = self.name.strip()
        if not 1 <= len(normalized) <= 64: raise ValueError("character_name_length_invalid")
        if normalized != self.name or any(ord(ch) < 32 for ch in self.name): raise ValueError("character_name_invalid")
        if not self.class_key.strip(): raise ValueError("class_key_required")
        if self.level < 1: raise ValueError("character_level_invalid")
        if self.experience < 0: raise ValueError("character_experience_invalid")
        if not self.location_key.strip(): raise ValueError("location_key_required")
        if self.current_hp < 0: raise ValueError("current_hp_invalid")
        if self.current_mp is not None and self.current_mp < 0: raise ValueError("current_mp_invalid")
        if self.version < 0: raise ValueError("character_version_invalid")

    def reset(self, *, location_key: str, current_hp: int, current_mp: int | None) -> Character:
        """Reset progression and current resources without changing identity, name, or class."""
        return replace(self, level=1, experience=0, location_key=location_key, current_hp=current_hp, current_mp=current_mp, version=self.version + 1)
