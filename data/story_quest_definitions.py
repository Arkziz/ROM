"""Canonical immutable story-quest definitions, statuses and validators.

This module is data-only. It does not access SQLite, Telegram, combat, inventory,
or other mutable runtime systems.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Optional, Sequence, Tuple

class QuestDefinitionError(ValueError):
    """Static story-quest content violates the canonical schema."""

class QuestType(str, Enum):
    TALK='TALK'; KILL_REGION='KILL_REGION'; QUEST_ITEM='QUEST_ITEM'; TURN_IN='TURN_IN'; BOSS='BOSS'

class PersistentQuestStatus(str, Enum):
    ACTIVE='ACTIVE'; COMPLETED='COMPLETED'; SKIPPED='SKIPPED'

class DerivedQuestStatus(str, Enum):
    LOCKED='LOCKED'; AVAILABLE='AVAILABLE'

@dataclass(frozen=True)
class RewardDefinition:
    """Candidate reward payload. Final values remain balance-controlled content."""
    exp: int=0
    gold: float=0.0
    item_keys: Tuple[str,...]=()

@dataclass(frozen=True)
class QuestItemDefinition:
    """Non-economic item stored outside ordinary inventory slots.

    ``consume_on_completion`` is false only when a collected clue must survive
    its QUEST_ITEM quest for a later approved turn-in.
    """
    item_key: str
    display_name: str
    required_quantity: int
    drop_chance: float
    consume_on_completion: bool = True

@dataclass(frozen=True)
class RequiredQuestItemDefinition:
    """Prerequisite item checked at interaction and optionally consumed."""
    item_key: str
    quantity: int
    consume: bool = True

@dataclass(frozen=True)
class NavigationDefinition:
    """Stable references later resolved by the canonical NPC registry."""
    location_id: str
    giver_npc_id: str
    turn_in_npc_id: Optional[str]=None
    objective_hint: str=''
    next_step_hint: str=''

@dataclass(frozen=True)
class StoryQuestDefinition:
    """Immutable canonical definition of one sequential story quest."""
    quest_id: str
    number: int
    title: str
    quest_type: QuestType
    location_id: str
    unlock_level: int
    previous_quest_id: Optional[str]
    giver_npc_id: str
    turn_in_npc_id: Optional[str]
    description: str
    objective_text: str
    target_quantity: int=1
    boss_key: Optional[str]=None
    quest_item: Optional[QuestItemDefinition]=None
    required_quest_items: Tuple[RequiredQuestItemDefinition, ...]=()
    quest_item_consumption: str = "default"
    reward: RewardDefinition=field(default_factory=RewardDefinition)
    navigation: Optional[NavigationDefinition]=None

def _require(value, message):
    if not value: raise QuestDefinitionError(message)

def _text(value):
    return isinstance(value,str) and bool(value.strip())

def validate_story_quest_definition(quest: StoryQuestDefinition) -> None:
    """Validate one definition without consulting mutable runtime state."""
    _require(_text(quest.quest_id),'quest_id must be non-empty')
    _require(quest.number>0,f'{quest.quest_id}: number must be positive')
    _require(_text(quest.title),f'{quest.quest_id}: title is required')
    _require(isinstance(quest.quest_type,QuestType),f'{quest.quest_id}: invalid quest_type')
    _require(_text(quest.location_id),f'{quest.quest_id}: location_id is required')
    _require(quest.unlock_level>0,f'{quest.quest_id}: unlock_level must be positive')
    _require(_text(quest.giver_npc_id),f'{quest.quest_id}: giver_npc_id is required')
    _require(_text(quest.description),f'{quest.quest_id}: description is required')
    _require(_text(quest.objective_text),f'{quest.quest_id}: objective_text is required')
    _require(quest.target_quantity>0,f'{quest.quest_id}: target_quantity must be positive')
    _require(quest.reward.exp>=0 and quest.reward.gold>=0,f'{quest.quest_id}: rewards cannot be negative')
    if quest.quest_type is QuestType.QUEST_ITEM:
        _require(quest.quest_item is not None,f'{quest.quest_id}: QUEST_ITEM requires quest_item')
        item=quest.quest_item
        _require(_text(item.item_key) and _text(item.display_name),f'{quest.quest_id}: quest item identity is required')
        _require(item.required_quantity>0,f'{quest.quest_id}: required_quantity must be positive')
        _require(0<=item.drop_chance<=1,f'{quest.quest_id}: drop_chance must be within 0..1')
        _require(isinstance(item.consume_on_completion,bool),f'{quest.quest_id}: consume_on_completion must be bool')
        _require(quest.target_quantity==item.required_quantity,f'{quest.quest_id}: quantities must match')
    else:
        _require(quest.quest_item is None,f'{quest.quest_id}: quest_item only allowed for QUEST_ITEM')
    if quest.quest_type is QuestType.BOSS:
        _require(_text(quest.boss_key),f'{quest.quest_id}: BOSS requires boss_key')
    else:
        _require(quest.boss_key is None,f'{quest.quest_id}: boss_key only allowed for BOSS')
    if quest.quest_type is QuestType.TURN_IN:
        _require(_text(quest.turn_in_npc_id),f'{quest.quest_id}: TURN_IN requires turn_in_npc_id')
    allowed_consumption = {"default", "none", "atomic_exact_once", "atomic_exact_once_all_or_nothing"}
    _require(quest.quest_item_consumption in allowed_consumption,f'{quest.quest_id}: invalid quest_item_consumption')
    required_keys=set()
    for required in quest.required_quest_items:
        _require(isinstance(required,RequiredQuestItemDefinition),f'{quest.quest_id}: invalid required quest item')
        _require(_text(required.item_key),f'{quest.quest_id}: required item key is required')
        _require(required.quantity>0,f'{quest.quest_id}: required item quantity must be positive')
        _require(isinstance(required.consume,bool),f'{quest.quest_id}: required item consume must be bool')
        _require(required.item_key not in required_keys,f'{quest.quest_id}: duplicate required item key')
        required_keys.add(required.item_key)
    if quest.quest_item_consumption == "none":
        _require(all(not item.consume for item in quest.required_quest_items),f'{quest.quest_id}: none policy cannot consume items')
    if quest.quest_item_consumption == "atomic_exact_once_all_or_nothing":
        _require(len(quest.required_quest_items)>1,f'{quest.quest_id}: all-or-nothing requires multiple items')
    if quest.navigation:
        _require(quest.navigation.location_id==quest.location_id,f'{quest.quest_id}: navigation location mismatch')
        _require(quest.navigation.giver_npc_id==quest.giver_npc_id,f'{quest.quest_id}: navigation giver mismatch')
        _require(quest.navigation.turn_in_npc_id==quest.turn_in_npc_id,f'{quest.quest_id}: navigation turn-in mismatch')

def validate_story_quest_pack(quests: Sequence[StoryQuestDefinition]):
    """Validate an ordered pack and return an immutable quest-ID registry."""
    _require(bool(quests),'story quest pack cannot be empty')
    by_id={}; numbers=set(); item_keys=set()
    for index,quest in enumerate(quests):
        validate_story_quest_definition(quest)
        _require(quest.quest_id not in by_id,f'duplicate quest_id: {quest.quest_id}')
        _require(quest.number not in numbers,f'duplicate quest number: {quest.number}')
        if index:
            previous=quests[index-1]
            _require(quest.previous_quest_id==previous.quest_id,f'{quest.quest_id}: invalid predecessor')
            _require(quest.number==previous.number+1,f'{quest.quest_id}: numbers must be consecutive')
        if quest.quest_item:
            _require(quest.quest_item.item_key not in item_keys,f'duplicate quest item key: {quest.quest_item.item_key}')
            item_keys.add(quest.quest_item.item_key)
        by_id[quest.quest_id]=quest; numbers.add(quest.number)
    return MappingProxyType(by_id)

def derive_story_quest_status(*,persistent_status,player_level,unlock_level,predecessor_completed,another_active_quest):
    """Return persistent status or derive LOCKED/AVAILABLE without storing it."""
    if persistent_status is not None: return persistent_status
    if player_level<unlock_level or not predecessor_completed or another_active_quest: return DerivedQuestStatus.LOCKED
    return DerivedQuestStatus.AVAILABLE

# Fixtures cover every objective family but are not production story content.
def _q(qid,num,qtype,prev=None,**kw):
    base=dict(quest_id=qid,number=num,title='Schema Fixture',quest_type=qtype,location_id='fixture_location',unlock_level=1,previous_quest_id=prev,giver_npc_id='fixture_npc',turn_in_npc_id=None,description='Schema fixture.',objective_text='Validate schema.',navigation=NavigationDefinition('fixture_location','fixture_npc'))
    base.update(kw); return StoryQuestDefinition(**base)
SCHEMA_FIXTURES=(
    _q('fixture_talk',1,QuestType.TALK),
    _q('fixture_kill_region',2,QuestType.KILL_REGION,'fixture_talk',target_quantity=2),
    _q('fixture_quest_item',3,QuestType.QUEST_ITEM,'fixture_kill_region',turn_in_npc_id='fixture_npc',target_quantity=1,quest_item=QuestItemDefinition('fixture_item','Fixture Item',1,0.5),navigation=NavigationDefinition('fixture_location','fixture_npc','fixture_npc')),
    _q('fixture_turn_in',4,QuestType.TURN_IN,'fixture_quest_item',turn_in_npc_id='fixture_npc',navigation=NavigationDefinition('fixture_location','fixture_npc','fixture_npc')),
    _q('fixture_boss',5,QuestType.BOSS,'fixture_turn_in',boss_key='fixture_boss_key'),
)
SCHEMA_FIXTURE_REGISTRY=validate_story_quest_pack(SCHEMA_FIXTURES)
