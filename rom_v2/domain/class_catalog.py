"""Source-faithful ROM V2 class catalog derived from the accepted V1 audit."""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

@dataclass(frozen=True, slots=True)
class CharacterClassDefinition:
    """Describe only class facts explicitly confirmed by the V1 parity audit."""
    key: str
    display_name: str
    description: str
    resource_key: str
    armor_type: str
    main_hand_subtypes: tuple[str, ...]
    off_hand_subtypes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.key or self.key != self.key.lower():
            raise ValueError("class_key_invalid")
        if not self.display_name.strip():
            raise ValueError("class_display_name_required")
        if not self.description.strip():
            raise ValueError("class_description_required")
        if not self.resource_key.strip():
            raise ValueError("class_resource_key_required")
        if self.armor_type not in {"cloth", "leather", "chain", "plate"}:
            raise ValueError("class_armor_type_invalid")
        if len(set(self.main_hand_subtypes)) != len(self.main_hand_subtypes):
            raise ValueError("class_main_hand_duplicate")
        if len(set(self.off_hand_subtypes)) != len(self.off_hand_subtypes):
            raise ValueError("class_off_hand_duplicate")

class ClassCatalog:
    """Resolve the exact six audited V1 class definitions by stable key."""
    def __init__(self, definitions: tuple[CharacterClassDefinition, ...]) -> None:
        if len(definitions) != 6:
            raise ValueError("class_catalog_requires_six_classes")
        by_key={item.key:item for item in definitions}
        if len(by_key) != len(definitions):
            raise ValueError("class_catalog_duplicate_key")
        self._by_key: Mapping[str, CharacterClassDefinition]=MappingProxyType(by_key)

    def find(self, key: str) -> CharacterClassDefinition | None:
        return self._by_key.get(key)

    def require(self, key: str) -> CharacterClassDefinition:
        result=self.find(key)
        if result is None:
            raise KeyError("class_key_unknown")
        return result

    def all(self) -> tuple[CharacterClassDefinition, ...]:
        return tuple(self._by_key.values())

# This tuple is intentionally a direct transcription of Stage 21.6.3 audit evidence.
# It must not be expanded through generic RPG assumptions.
DEFAULT_CLASS_CATALOG: Final[ClassCatalog] = ClassCatalog((
    CharacterClassDefinition("warrior","🛡️ Воїн","Фізичний боєць ближнього бою.\nОсновні характеристики: Сила, Витривалість.\nРесурс у бою: 🔴 Лютість.","rage","chain",("sword_1h","sword_2h"),("warrior_shield",)),
    CharacterClassDefinition("knight","⚔️ Лицар","Захисник із високим фізичним захистом і щитом.\nОсновні характеристики: Витривалість, Фіз. захист.\nРесурс у бою: 🔴 Лютість.","rage","plate",("sword_1h",),("shield",)),
    CharacterClassDefinition("scout","🏹 Скаут","Дистанційний фізичний боєць із пастками та точними пострілами.\nОсновні характеристики: Спритність, Сила.\nРесурс у бою: 🟡 Енергія.","combat_energy","leather",("bow_2h","crossbow_2h"),()),
    CharacterClassDefinition("rogue","🗡️ Розбійник","Швидкий боєць ближнього бою з майбутньою механікою комбо.\nОсновні характеристики: Спритність, Сила.\nРесурс у бою: 🟡 Енергія + комбо-очки.","combat_energy_combo","leather",("dagger_1h",),("dagger",)),
    CharacterClassDefinition("mage","🔮 Маг","Магічний боєць із високим вибуховою шкодою.\nОсновні характеристики: Інтелект, Мудрість.\nРесурс у бою: 🔵 Мана.","mana","cloth",("wand_1h","staff_2h"),("talisman",)),
    CharacterClassDefinition("priest","⚕️ Жрець","Магічний клас підтримки з лікуванням і захистом.\nОсновні характеристики: Мудрість, Інтелект.\nРесурс у бою: 🔵 Мана.","mana","cloth",("wand_1h","staff_2h"),("talisman",)),
))
