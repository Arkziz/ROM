"""V1-parity item definition and owned inventory-instance identities."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping


def _positive(value: int, field: str) -> int:
    value=int(value)
    if value <= 0: raise ValueError(f"{field}_must_be_positive")
    return value


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    """Stable catalog identity shared by zero or more owned inventory rows."""
    item_id: int
    name: str
    item_type: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self,"item_id",_positive(self.item_id,"item_id"))
        if not self.name.strip(): raise ValueError("item_name_required")
        if not self.item_type.strip(): raise ValueError("item_type_required")
        object.__setattr__(self,"metadata",dict(self.metadata))


@dataclass(frozen=True, slots=True)
class ItemInstance:
    """One owned inventory row; identity is never inferred from its definition."""
    inventory_id: int
    owner_user_id: int
    item_id: int
    quantity: int = 1
    instance_metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self,"inventory_id",_positive(self.inventory_id,"inventory_id"))
        object.__setattr__(self,"owner_user_id",_positive(self.owner_user_id,"owner_user_id"))
        object.__setattr__(self,"item_id",_positive(self.item_id,"item_id"))
        object.__setattr__(self,"quantity",_positive(self.quantity,"quantity"))
        object.__setattr__(self,"instance_metadata",dict(self.instance_metadata or {}))

    def with_quantity(self, quantity: int) -> "ItemInstance":
        return ItemInstance(self.inventory_id,self.owner_user_id,self.item_id,quantity,self.instance_metadata)


@dataclass(frozen=True, slots=True)
class StoryQuestItemIdentity:
    """Virtual quest-item balance identity, deliberately separate from inventory."""
    user_id: int
    quest_id: int
    item_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self,"user_id",_positive(self.user_id,"user_id"))
        object.__setattr__(self,"quest_id",_positive(self.quest_id,"quest_id"))
        if not self.item_key.strip(): raise ValueError("item_key_required")
